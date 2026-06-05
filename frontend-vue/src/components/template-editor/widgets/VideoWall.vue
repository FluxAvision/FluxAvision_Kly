<script setup lang="ts">
/**
 * 视频墙组件 - 支持多宫格布局，直接使用存储的设备信息+RTSP地址渲染
 */
import { computed } from 'vue'
import { Monitor } from 'lucide-vue-next'
import RTSPVideoPlayer from '@/components/video/RTSPVideoPlayer.vue'
import type { ComponentConfig } from '@/types/template-editor'

const props = defineProps<{
  config: ComponentConfig
  data?: Record<string, any>
}>()

// 宫格配置
const gridCols = computed(() => props.config.props?.gridCols ?? 2)
const gridRows = computed(() => props.config.props?.gridRows ?? 1)
const totalCells = computed(() => gridCols.value * gridRows.value)

// 直接读取存储的字段，补齐到总格子数
const cellDeviceIds = computed<string[]>(() => {
  const ids = props.config.props?.cellDeviceIds ?? []
  while (ids.length < totalCells.value) ids.push('')
  return ids.slice(0, totalCells.value)
})

const cellDeviceNames = computed<string[]>(() => {
  const names = props.config.props?.cellDeviceNames ?? []
  while (names.length < totalCells.value) names.push('')
  return names.slice(0, totalCells.value)
})

const cellDeviceIps = computed<string[]>(() => {
  const ips = props.config.props?.cellDeviceIps ?? []
  while (ips.length < totalCells.value) ips.push('')
  return ips.slice(0, totalCells.value)
})

const cellRtspUrls = computed<string[]>(() => {
  const urls = props.config.props?.cellRtspUrls ?? []
  while (urls.length < totalCells.value) urls.push('')
  return urls.slice(0, totalCells.value)
})

// 自动播放
const autoPlay = computed(() => props.config.props?.autoPlay ?? true)
// 静音
const muted = computed(() => props.config.props?.muted ?? true)

// 网格模板
const gridTemplateColumns = computed(() => `repeat(${gridCols.value}, 1fr)`)
const gridTemplateRows = computed(() => `repeat(${gridRows.value}, 1fr)`)

// 格子边框样式
const cellBorderStyle = computed(() => {
  const w = props.config.props?.cellBorderWidth ?? 1
  const c = props.config.props?.cellBorderColor ?? '#1e293b'
  return {
    borderWidth: `${w}px`,
    borderColor: c,
    borderStyle: 'solid',
  }
})

// 占位背景
const placeholderBg = computed(() => props.config.props?.placeholderBg ?? '#0d1421')
</script>

<template>
  <div
    class="w-full h-full overflow-hidden"
    :style="{
      display: 'grid',
      gridTemplateColumns,
      gridTemplateRows,
      gap: '2px',
      backgroundColor: config.styles?.backgroundColor || 'transparent',
    }"
  >
    <div
      v-for="(_, index) in cellDeviceIds"
      :key="index"
      class="relative flex items-center justify-center overflow-hidden"
      :style="{
        ...cellBorderStyle,
        backgroundColor: placeholderBg,
      }"
    >
      <!-- 有设备时直接使用存储的 RTSP 地址和设备信息渲染 -->
      <template v-if="cellDeviceIds[index]">
        <RTSPVideoPlayer
          :device-id="cellDeviceIds[index]"
          :rtsp-url="cellRtspUrls[index] || undefined"
          :name="cellDeviceNames[index]"
          :auto-play="autoPlay"
          :compact="true"
          :show-controls="false"
          class="absolute inset-0 w-full h-full"
        />
      </template>

      <!-- 无设备时显示占位 -->
      <div
        v-else
        class="flex flex-col items-center justify-center gap-1 text-[#5a6a80]"
      >
        <Monitor class="w-6 h-6" />
        <span class="text-xs">请选择设备</span>
      </div>
    </div>
  </div>
</template>
