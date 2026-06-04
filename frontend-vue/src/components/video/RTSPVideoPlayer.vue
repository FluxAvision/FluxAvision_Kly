<script setup lang="ts">
import { ref, computed, shallowRef, watch, onMounted, onUnmounted, nextTick } from 'vue'
import {
  AlertTriangle,
  Loader2,
  Maximize2,
  Minimize2,
  RefreshCw,
  WifiOff,
} from 'lucide-vue-next'

const props = withDefaults(defineProps<{
  deviceId: string
  rtspUrl?: string
  status?: string
  name?: string
  autoPlay?: boolean
  className?: string
  showControls?: boolean
  compact?: boolean
}>(), {
  status: 'online',
  name: '',
  autoPlay: true,
  className: '',
  showControls: true,
  compact: false,
})

type PlayerStatus = 'connecting' | 'playing' | 'error' | 'offline'

const POLL_INTERVAL = 200
const ERROR_RETRY_INTERVAL = 3000
const ERROR_MAX_RETRIES = 10
const MAX_FRAME_DECODE_MS = 100

const canvasRef = ref<HTMLCanvasElement>()
const containerRef = ref<HTMLDivElement>()
const pollTimerRef = shallowRef<ReturnType<typeof setInterval> | null>(null)
const retryTimerRef = shallowRef<ReturnType<typeof setTimeout> | null>(null)
const wsRef = shallowRef<WebSocket | null>(null)
const retryCountRef = ref(0)
const statusRef = ref<PlayerStatus>('connecting')
const usePollingRef = ref(false)
const frameDecodingRef = ref(false)
const frameTokenRef = ref(0)

const playerStatus = ref<PlayerStatus>(props.status === 'online' ? 'connecting' : 'offline')
const isFullscreen = ref(false)

const effectiveStatus = computed(() => props.status === 'offline' ? 'offline' : playerStatus.value)

const snapshotUrl = `/api/devices/${props.deviceId}/snapshot`

function updateStatus(newStatus: PlayerStatus) {
  statusRef.value = newStatus
  playerStatus.value = newStatus
}

function clearTimers() {
  if (pollTimerRef.value) {
    clearInterval(pollTimerRef.value)
    pollTimerRef.value = null
  }
  if (retryTimerRef.value) {
    clearTimeout(retryTimerRef.value)
    retryTimerRef.value = null
  }
}

function closeWebSocket() {
  if (wsRef.value) {
    const ws = wsRef.value
    wsRef.value = null
    ws.onopen = null
    ws.onmessage = null
    ws.onerror = null
    ws.onclose = null
    ws.close()
  }
}

function clearAll() {
  clearTimers()
  closeWebSocket()
  frameDecodingRef.value = false
  frameTokenRef.value = 0
}

function buildWebSocketUrl(): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const hostname = window.location.hostname
  const backendPort = window.location.port === '3000' ? '15678' : window.location.port
  return `${protocol}//${hostname}:${backendPort}/api/devices/${props.deviceId}/stream/ws`
}

/**
 * 在 Canvas 上绘制一帧画面。
 * 使用 createImageBitmap 解码 Blob，然后 drawImage 到 Canvas。
 * 如果前一帧仍在解码，丢弃新帧（帧丢弃机制）。
 */
async function renderFrameToCanvas(blob: Blob, token: number): Promise<void> {
  if (!canvasRef.value || token !== frameTokenRef.value) return
  if (frameDecodingRef.value) return  // 丢弃：前一帧还在解码中

  frameDecodingRef.value = true
  try {
    // 使用 ImageBitmap 解码（浏览器优化路径，比 Image 对象更高效）
    const bitmap = await createImageBitmap(blob)
    if (token !== frameTokenRef.value) {
      // 在解码过程中已被更新的帧替代，丢弃
      bitmap.close()
      return
    }

    const canvas = canvasRef.value
    // 调整 Canvas 尺寸匹配 Bitmap（避免每次 setAttribute 导致重排）
    if (canvas.width !== bitmap.width || canvas.height !== bitmap.height) {
      canvas.width = bitmap.width
      canvas.height = bitmap.height
    }
    const ctx = canvas.getContext('2d')
    if (ctx) {
      ctx.drawImage(bitmap, 0, 0)
    }
    bitmap.close()

    updateStatus('playing')
    retryCountRef.value = 0
  } catch (e) {
    // 如果 createImageBitmap 失败（较老浏览器），回退到 Image 方式
    try {
      const url = URL.createObjectURL(blob)
      if (token !== frameTokenRef.value) {
        URL.revokeObjectURL(url)
        return
      }
      const img = new Image()
      await new Promise<void>((resolve, reject) => {
        img.onload = () => {
          URL.revokeObjectURL(url)
          if (token !== frameTokenRef.value) {
            reject(new Error('stale frame'))
            return
          }
          const canvas = canvasRef.value!
          if (canvas.width !== img.naturalWidth || canvas.height !== img.naturalHeight) {
            canvas.width = img.naturalWidth
            canvas.height = img.naturalHeight
          }
          const ctx = canvas.getContext('2d')
          if (ctx) ctx.drawImage(img, 0, 0)
          resolve()
        }
        img.onerror = () => {
          URL.revokeObjectURL(url)
          reject(new Error('image decode error'))
        }
        img.src = url
      })
      updateStatus('playing')
      retryCountRef.value = 0
    } catch {
      // decode failed silently
    }
  } finally {
    frameDecodingRef.value = false
  }
}

function startPolling() {
  clearAll()
  usePollingRef.value = true
  updateStatus('connecting')

  let consecutiveErrors = 0

  pollTimerRef.value = setInterval(async () => {
    const token = ++frameTokenRef.value
    try {
      const res = await fetch(`${snapshotUrl}?t=${Date.now()}`)
      if (!res.ok) {
        consecutiveErrors++
        if (consecutiveErrors >= 5) {
          updateStatus('error')
          clearTimers()
          if (retryCountRef.value >= ERROR_MAX_RETRIES) return
          retryCountRef.value += 1
          retryTimerRef.value = setTimeout(() => {
            startPolling()
          }, ERROR_RETRY_INTERVAL)
        }
        return
      }
      consecutiveErrors = 0
      const blob = await res.blob()
      renderFrameToCanvas(blob, token)
    } catch {
      consecutiveErrors++
      if (consecutiveErrors >= 5) {
        updateStatus('error')
        clearTimers()
        if (retryCountRef.value >= ERROR_MAX_RETRIES) return
        retryCountRef.value += 1
        retryTimerRef.value = setTimeout(() => {
          startPolling()
        }, ERROR_RETRY_INTERVAL)
      }
    }
  }, POLL_INTERVAL)
}

function startWebSocket() {
  clearAll()
  usePollingRef.value = false
  updateStatus('connecting')

  const ws = new WebSocket(buildWebSocketUrl())
  ws.binaryType = 'blob'
  wsRef.value = ws

  ws.onopen = () => {
    updateStatus('connecting')
  }

  ws.onmessage = (event: MessageEvent) => {
    if (event.data instanceof Blob) {
      const token = ++frameTokenRef.value
      renderFrameToCanvas(event.data, token)
    }
  }

  ws.onerror = () => {
    console.log('[RTSPVideoPlayer] WebSocket 预览失败，降级到快照轮询')
    startPolling()
  }

  ws.onclose = () => {
    if (statusRef.value === 'offline') return
    if (!usePollingRef.value) {
      startPolling()
    }
  }
}

function handleRefresh() {
  retryCountRef.value = 0
  startWebSocket()
}

function handleFullscreen() {
  if (!containerRef.value) return

  if (!document.fullscreenElement) {
    containerRef.value.requestFullscreen()
      .then(() => { isFullscreen.value = true })
      .catch(() => {})
  } else {
    document.exitFullscreen()
      .then(() => { isFullscreen.value = false })
      .catch(() => {})
  }
}

watch(() => props.deviceId, () => {
  clearAll()
  if (props.status !== 'offline' && props.autoPlay) {
    startWebSocket()
  }
})

onMounted(() => {
  if (props.status === 'offline') {
    clearAll()
    statusRef.value = 'offline'
    return
  }
  if (props.autoPlay) {
    setTimeout(() => startWebSocket(), 0)
  }
})

onUnmounted(() => {
  clearAll()
})
</script>

<template>
  <div
    ref="containerRef"
    class="relative overflow-hidden bg-black"
    :class="className"
    :style="{ minHeight: compact ? '120px' : '200px' }"
  >
    <!-- Canvas 渲染层 -->
    <canvas
      ref="canvasRef"
      class="absolute inset-0 h-full w-full"
      :style="{
        objectFit: 'contain',
        display: effectiveStatus === 'playing' ? 'block' : 'none'
      }"
    />

    <!-- Offline overlay -->
    <div v-if="effectiveStatus === 'offline'" class="absolute inset-0 flex items-center justify-center bg-black/60">
      <div class="text-center">
        <WifiOff class="mx-auto mb-2 h-8 w-8 text-[#ef4444]/70" />
        <p class="text-xs text-[#8892a0]">设备离线</p>
      </div>
    </div>

    <!-- Connecting overlay -->
    <div v-else-if="effectiveStatus === 'connecting'" class="absolute inset-0 flex items-center justify-center bg-black/40">
      <div class="text-center">
        <Loader2 class="mx-auto mb-2 h-8 w-8 animate-spin text-[#00d9ff]" />
        <p class="text-xs text-[#8892a0]">视频连接中...</p>
      </div>
    </div>

    <!-- Error overlay -->
    <div
      v-else-if="effectiveStatus === 'error'"
      class="absolute inset-0 flex cursor-pointer items-center justify-center bg-black/50"
      @click="handleRefresh"
    >
      <div class="text-center">
        <AlertTriangle class="mx-auto mb-2 h-8 w-8 text-[#ff9500]" />
        <p class="mb-1 text-xs text-[#8892a0]">视频连接失败</p>
        <p class="text-[10px] text-[#8892a0]/60">点击重试</p>
      </div>
    </div>

    <!-- Controls -->
    <div v-if="showControls" class="absolute right-0 top-0 z-10 flex items-center gap-1 p-1.5">
      <button
        class="flex h-6 w-6 cursor-pointer items-center justify-center rounded bg-black/50 text-white/70 transition-colors hover:bg-black/70 hover:text-white"
        title="刷新视频"
        @click="handleRefresh"
      >
        <RefreshCw class="h-3.5 w-3.5" :class="{ 'animate-spin': effectiveStatus === 'connecting' }" />
      </button>
      <button
        v-if="!compact"
        class="flex h-6 w-6 cursor-pointer items-center justify-center rounded bg-black/50 text-white/70 transition-colors hover:bg-black/70 hover:text-white"
        :title="isFullscreen ? '退出全屏' : '全屏'"
        @click="handleFullscreen"
      >
        <Minimize2 v-if="isFullscreen" class="h-3.5 w-3.5" />
        <Maximize2 v-else class="h-3.5 w-3.5" />
      </button>
    </div>

    <!-- Name label -->
    <div v-if="name && !compact" class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent px-2 py-1">
      <p class="truncate text-[10px] text-white/80">{{ name }}</p>
    </div>
  </div>
</template>
