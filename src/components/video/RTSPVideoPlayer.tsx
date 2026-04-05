'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import {
  AlertTriangle,
  Loader2,
  Maximize2,
  Minimize2,
  RefreshCw,
  WifiOff,
} from 'lucide-react'

interface RTSPVideoPlayerProps {
  deviceId: string
  rtspUrl?: string
  status?: string
  name?: string
  autoPlay?: boolean
  className?: string
  showControls?: boolean
  compact?: boolean
  onStatusChange?: (status: 'connecting' | 'playing' | 'error' | 'offline') => void
}

type PlayerStatus = 'connecting' | 'playing' | 'error' | 'offline'

const POLL_INTERVAL = 200
const ERROR_RETRY_INTERVAL = 3000
const ERROR_MAX_RETRIES = 10

export default function RTSPVideoPlayer({
  deviceId,
  status = 'online',
  name = '',
  autoPlay = true,
  className = '',
  showControls = true,
  compact = false,
  onStatusChange,
}: RTSPVideoPlayerProps) {
  const imgRef = useRef<HTMLImageElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const retryCountRef = useRef(0)
  const statusRef = useRef<PlayerStatus>('connecting')
  const usePollingRef = useRef(false)
  const startPollingRef = useRef<() => void>(() => {})
  const objectUrlRef = useRef<string | null>(null)
  const frameTokenRef = useRef(0)
  const [playerStatus, setPlayerStatus] = useState<PlayerStatus>(
    status === 'online' ? 'connecting' : 'offline'
  )
  const [isFullscreen, setIsFullscreen] = useState(false)
  const effectiveStatus: PlayerStatus = status === 'offline' ? 'offline' : playerStatus

  const snapshotUrl = `/api/devices/${deviceId}/snapshot`

  const updateStatus = useCallback((newStatus: PlayerStatus) => {
    statusRef.current = newStatus
    setPlayerStatus(newStatus)
    onStatusChange?.(newStatus)
  }, [onStatusChange])

  const revokeObjectUrl = useCallback(() => {
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current)
      objectUrlRef.current = null
    }
  }, [])

  const clearTimers = useCallback(() => {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current)
      pollTimerRef.current = null
    }
    if (retryTimerRef.current) {
      clearTimeout(retryTimerRef.current)
      retryTimerRef.current = null
    }
  }, [])

  const closeWebSocket = useCallback(() => {
    if (wsRef.current) {
      const ws = wsRef.current
      wsRef.current = null
      ws.onopen = null
      ws.onmessage = null
      ws.onerror = null
      ws.onclose = null
      ws.close()
    }
  }, [])

  const clearAll = useCallback(() => {
    clearTimers()
    closeWebSocket()
    revokeObjectUrl()
    if (imgRef.current) {
      imgRef.current.src = ''
    }
  }, [clearTimers, closeWebSocket, revokeObjectUrl])

  const buildWebSocketUrl = useCallback(() => {
    if (typeof window === 'undefined') {
      return ''
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const hostname = window.location.hostname
    const backendPort = window.location.port === '3000' ? '8080' : window.location.port
    return `${protocol}//${hostname}:${backendPort}/api/devices/${deviceId}/stream/ws`
  }, [deviceId])

  const applyFrame = useCallback((frame: Blob) => {
    if (!imgRef.current) {
      return
    }

    const token = ++frameTokenRef.current
    const nextUrl = URL.createObjectURL(frame)
    const img = imgRef.current

    img.onload = () => {
      if (token !== frameTokenRef.current) {
        URL.revokeObjectURL(nextUrl)
        return
      }

      revokeObjectUrl()
      objectUrlRef.current = nextUrl
      updateStatus('playing')
      retryCountRef.current = 0
      img.onload = null
    }

    img.onerror = () => {
      URL.revokeObjectURL(nextUrl)
      img.onerror = null
    }

    img.src = nextUrl
  }, [revokeObjectUrl, updateStatus])

  const startPolling = useCallback(() => {
    clearAll()
    usePollingRef.current = true
    updateStatus('connecting')

    let consecutiveErrors = 0
    pollTimerRef.current = setInterval(() => {
      const timestamp = Date.now()
      const testImg = new Image()

      testImg.onload = () => {
        consecutiveErrors = 0
        if (imgRef.current) {
          imgRef.current.src = `${snapshotUrl}?t=${timestamp}`
        }
        updateStatus('playing')
        retryCountRef.current = 0
      }

      testImg.onerror = () => {
        consecutiveErrors += 1
        if (consecutiveErrors >= 5) {
          updateStatus('error')
          clearTimers()
          if (retryCountRef.current >= ERROR_MAX_RETRIES) {
            return
          }

          retryCountRef.current += 1
          retryTimerRef.current = setTimeout(() => {
            startPollingRef.current()
          }, ERROR_RETRY_INTERVAL)
        }
      }

      testImg.src = `${snapshotUrl}?t=${timestamp}`
    }, POLL_INTERVAL)
  }, [clearAll, clearTimers, snapshotUrl, updateStatus])

  const startWebSocket = useCallback(() => {
    clearAll()
    usePollingRef.current = false
    updateStatus('connecting')

    const ws = new WebSocket(buildWebSocketUrl())
    ws.binaryType = 'blob'
    wsRef.current = ws

    ws.onopen = () => {
      updateStatus('connecting')
    }

    ws.onmessage = (event) => {
      if (event.data instanceof Blob) {
        applyFrame(event.data)
      }
    }

    ws.onerror = () => {
      logger.info('WebSocket 预览失败，降级到快照轮询')
      startPolling()
    }

    ws.onclose = () => {
      if (statusRef.current === 'offline') {
        return
      }
      if (!usePollingRef.current) {
        startPolling()
      }
    }
  }, [applyFrame, buildWebSocketUrl, clearAll, startPolling, updateStatus])

  useEffect(() => {
    startPollingRef.current = startPolling
  }, [startPolling])

  useEffect(() => {
    if (status === 'offline') {
      clearAll()
      statusRef.current = 'offline'
      onStatusChange?.('offline')
      return
    }

    if (autoPlay) {
      const timer = window.setTimeout(() => {
        startWebSocket()
      }, 0)

      return () => {
        window.clearTimeout(timer)
        clearAll()
      }
    }

    return () => {
      clearAll()
    }
  }, [autoPlay, clearAll, deviceId, startWebSocket, status, updateStatus])

  const handleRefresh = useCallback(() => {
    retryCountRef.current = 0
    startWebSocket()
  }, [startWebSocket])

  const handleFullscreen = useCallback(() => {
    if (!containerRef.current) {
      return
    }

    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen()
        .then(() => setIsFullscreen(true))
        .catch(() => {})
    } else {
      document.exitFullscreen()
        .then(() => setIsFullscreen(false))
        .catch(() => {})
    }
  }, [])

  const renderStatusOverlay = () => {
    switch (effectiveStatus) {
      case 'offline':
        return (
          <div className="absolute inset-0 flex items-center justify-center bg-black/60">
            <div className="text-center">
              <WifiOff className="mx-auto mb-2 h-8 w-8 text-[#ef4444]/70" />
              <p className="text-xs text-[#8892a0]">设备离线</p>
            </div>
          </div>
        )
      case 'connecting':
        return (
          <div className="absolute inset-0 flex items-center justify-center bg-black/40">
            <div className="text-center">
              <Loader2 className="mx-auto mb-2 h-8 w-8 animate-spin text-[#00d9ff]" />
              <p className="text-xs text-[#8892a0]">视频连接中...</p>
            </div>
          </div>
        )
      case 'error':
        return (
          <div
            className="absolute inset-0 flex cursor-pointer items-center justify-center bg-black/50"
            onClick={handleRefresh}
          >
            <div className="text-center">
              <AlertTriangle className="mx-auto mb-2 h-8 w-8 text-[#ff9500]" />
              <p className="mb-1 text-xs text-[#8892a0]">视频连接失败</p>
              <p className="text-[10px] text-[#8892a0]/60">点击重试</p>
            </div>
          </div>
        )
      default:
        return null
    }
  }

  return (
    <div
      ref={containerRef}
      className={`relative overflow-hidden bg-black ${className}`}
      style={{ minHeight: compact ? '120px' : '200px' }}
    >
      <img
        ref={imgRef}
        alt={name || '实时视频'}
        className="absolute inset-0 h-full w-full object-contain"
        style={{ display: effectiveStatus === 'playing' ? 'block' : 'none' }}
      />

      {effectiveStatus !== 'playing' && renderStatusOverlay()}

      {showControls && (
        <div className="absolute right-0 top-0 z-10 flex items-center gap-1 p-1.5">
          <button
            onClick={handleRefresh}
            className="flex h-6 w-6 cursor-pointer items-center justify-center rounded bg-black/50 text-white/70 transition-colors hover:bg-black/70 hover:text-white"
            title="刷新视频"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${effectiveStatus === 'connecting' ? 'animate-spin' : ''}`} />
          </button>

          {!compact && (
            <button
              onClick={handleFullscreen}
              className="flex h-6 w-6 cursor-pointer items-center justify-center rounded bg-black/50 text-white/70 transition-colors hover:bg-black/70 hover:text-white"
              title={isFullscreen ? '退出全屏' : '全屏'}
            >
              {isFullscreen ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
            </button>
          )}
        </div>
      )}

      {name && !compact && (
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent px-2 py-1">
          <p className="truncate text-[10px] text-white/80">{name}</p>
        </div>
      )}
    </div>
  )
}

const logger = {
  info: (msg: string) => console.log(`[RTSPVideoPlayer] ${msg}`),
}
