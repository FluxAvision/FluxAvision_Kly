'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import { WifiOff, AlertTriangle, Loader2, RefreshCw, Maximize2, Minimize2 } from 'lucide-react'

/**
 * RTSPVideoPlayer 组件（OpenCV MJPEG 方案）
 *
 * 通过 OpenCV 后端连接 RTSP 摄像头，以 MJPEG (Motion JPEG) 流方式推送到浏览器。
 * 浏览器原生 <img> 标签即可显示 MJPEG 流，无需任何额外 JS 库。
 *
 * 技术链路：
 *   摄像头(RTSP) → OpenCV VideoCapture → JPEG帧 → HTTP MJPEG流 → <img>
 *
 * 优势：
 *   - 无需 mpegts.js / flv.js 等第三方库
 *   - 无需 MSE (Media Source Extensions) 支持
 *   - 浏览器兼容性极佳（所有现代浏览器都支持 MJPEG）
 *   - 延迟约 100-300ms，满足实时监控需求
 *
 * 两种播放模式：
 *   1. MJPEG 流模式（默认）：通过 /api/devices/{id}/stream 获取连续 JPEG 流
 *   2. 轮询帧模式（降级）：通过 /api/devices/{id}/snapshot 定时获取单帧
 */

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

// 轮询帧模式配置
const POLL_INTERVAL = 100        // 轮询间隔（毫秒）
const ERROR_RETRY_INTERVAL = 5000 // 错误重试间隔（毫秒）
const ERROR_MAX_RETRIES = 10     // 最大重试次数

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
  const retryCountRef = useRef(0)
  const statusRef = useRef<PlayerStatus>('connecting')
  const usePollingRef = useRef(false)  // 是否降级到轮询模式

  const [playerStatus, setPlayerStatus] = useState<PlayerStatus>(
    status === 'online' ? 'connecting' : 'offline'
  )
  const [isFullscreen, setIsFullscreen] = useState(false)

  const streamUrl = `/api/devices/${deviceId}/stream`
  const snapshotUrl = `/api/devices/${deviceId}/snapshot`

  const updateStatus = useCallback((newStatus: PlayerStatus) => {
    statusRef.current = newStatus
    setPlayerStatus(newStatus)
    onStatusChange?.(newStatus)
  }, [onStatusChange])

  // 清理所有定时器
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

  // MJPEG 流模式
  const startMjpegStream = useCallback(() => {
    if (!imgRef.current) return

    clearTimers()
    usePollingRef.current = false
    updateStatus('connecting')

    const img = imgRef.current

    const handleLoad = () => {
      updateStatus('playing')
      retryCountRef.current = 0
    }

    const handleError = () => {
      if (statusRef.current === 'offline') return

      // MJPEG 流失败，降级到轮询模式
      logger.info('MJPEG 流连接失败，降级到轮询帧模式')
      usePollingRef.current = true
      startPolling()
    }

    img.onload = handleLoad
    img.onerror = handleError
    img.src = streamUrl
  }, [streamUrl, updateStatus, clearTimers])

  // 轮询帧模式（MJPEG 不兼容时的降级方案）
  const startPolling = useCallback(() => {
    clearTimers()
    updateStatus('connecting')

    let consecutiveErrors = 0

    pollTimerRef.current = setInterval(() => {
      if (!imgRef.current) return

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
        consecutiveErrors++
        if (consecutiveErrors >= 5) {
          updateStatus('error')
          clearTimers()
          scheduleRetry()
        }
      }

      testImg.src = `${snapshotUrl}?t=${timestamp}`
    }, POLL_INTERVAL)
  }, [snapshotUrl, updateStatus, clearTimers])

  // 错误后调度重试
  const scheduleRetry = useCallback(() => {
    clearTimers()

    if (retryCountRef.current >= ERROR_MAX_RETRIES) {
      return
    }

    retryCountRef.current++
    const delay = ERROR_RETRY_INTERVAL

    retryTimerRef.current = setTimeout(() => {
      if (usePollingRef.current) {
        startPolling()
      } else {
        startMjpegStream()
      }
    }, delay)
  }, [clearTimers, startPolling, startMjpegStream])

  // 初始化播放
  useEffect(() => {
    if (status === 'offline') {
      updateStatus('offline')
      return
    }

    if (autoPlay) {
      startMjpegStream()
    }

    return () => {
      clearTimers()
      if (imgRef.current) {
        imgRef.current.src = ''
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deviceId, status, autoPlay])

  // 手动刷新
  const handleRefresh = useCallback(() => {
    retryCountRef.current = 0
    clearTimers()
    usePollingRef.current = false

    if (imgRef.current) {
      imgRef.current.src = ''
      setTimeout(() => startMjpegStream(), 100)
    }
  }, [clearTimers, startMjpegStream])

  // 全屏切换
  const handleFullscreen = useCallback(() => {
    if (!containerRef.current) return
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {})
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(() => {})
    }
  }, [])

  // 渲染状态覆盖层
  const renderStatusOverlay = () => {
    switch (playerStatus) {
      case 'offline':
        return (
          <div className="absolute inset-0 flex items-center justify-center bg-black/60">
            <div className="text-center">
              <WifiOff className="w-8 h-8 mx-auto text-[#ef4444]/70 mb-2" />
              <p className="text-xs text-[#8892a0]">设备离线</p>
            </div>
          </div>
        )

      case 'connecting':
        return (
          <div className="absolute inset-0 flex items-center justify-center bg-black/40">
            <div className="text-center">
              <Loader2 className="w-8 h-8 mx-auto text-[#00d9ff] animate-spin mb-2" />
              <p className="text-xs text-[#8892a0]">视频流连接中...</p>
            </div>
          </div>
        )

      case 'error':
        return (
          <div className="absolute inset-0 flex items-center justify-center bg-black/50 cursor-pointer" onClick={handleRefresh}>
            <div className="text-center">
              <AlertTriangle className="w-8 h-8 mx-auto text-[#ff9500] mb-2" />
              <p className="text-xs text-[#8892a0] mb-1">视频连接失败</p>
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
      className={`relative bg-black overflow-hidden ${className}`}
      style={{ minHeight: compact ? '120px' : '200px' }}
    >
      {/* MJPEG Image Element — 浏览器原生支持 */}
      <img
        ref={imgRef}
        alt={name || '实时视频'}
        className="absolute inset-0 w-full h-full object-contain"
        style={{ display: playerStatus === 'playing' ? 'block' : 'none' }}
      />

      {/* Status Overlay */}
      {playerStatus !== 'playing' && renderStatusOverlay()}

      {/* Controls */}
      {showControls && (
        <div className="absolute top-0 right-0 flex items-center gap-1 p-1.5 z-10">
          <button
            onClick={handleRefresh}
            className="w-6 h-6 rounded bg-black/50 hover:bg-black/70 flex items-center justify-center text-white/70 hover:text-white transition-colors cursor-pointer"
            title="刷新视频"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${playerStatus === 'connecting' ? 'animate-spin' : ''}`} />
          </button>

          {!compact && (
            <button
              onClick={handleFullscreen}
              className="w-6 h-6 rounded bg-black/50 hover:bg-black/70 flex items-center justify-center text-white/70 hover:text-white transition-colors cursor-pointer"
              title={isFullscreen ? '退出全屏' : '全屏'}
            >
              {isFullscreen
                ? <Minimize2 className="w-3.5 h-3.5" />
                : <Maximize2 className="w-3.5 h-3.5" />
              }
            </button>
          )}
        </div>
      )}

      {/* Device name label */}
      {name && !compact && (
        <div className="absolute bottom-0 left-0 right-0 px-2 py-1 bg-gradient-to-t from-black/60 to-transparent">
          <p className="text-[10px] text-white/80 truncate">{name}</p>
        </div>
      )}
    </div>
  )
}

// 简单的 logger（避免依赖 console）
const logger = {
  info: (msg: string) => console.log(`[RTSPVideoPlayer] ${msg}`),
}
