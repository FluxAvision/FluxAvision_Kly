<script setup lang="ts">
import { computed } from 'vue'
import { X, Wifi, WifiOff, RefreshCw } from 'lucide-vue-next'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import RTSPVideoPlayer from '@/components/video/RTSPVideoPlayer.vue'
import type { HourlyData, Device, LargeScreenConfig } from '../composables/useLargeScreenData'

use([CanvasRenderer, BarChart, GridComponent, TooltipComponent])

const props = defineProps<{
  config: LargeScreenConfig
  metrics: Record<string, number>
  hourlyData: HourlyData[]
  devices: Device[]
  storeLogo: string
  loading: boolean
  clockTime: string
  getLabel: (key: string) => string
}>()

const emit = defineEmits<{ close: [] }>()

const centerMetric = computed(() => {
  const first = props.config.metrics[0]
  return first
    ? { key: first, label: props.getLabel(first), value: props.metrics[first] || 0 }
    : { key: 'currentIn', label: '当前在场', value: 0 }
})

const cornerMetrics = computed(() => {
  const rest = props.config.metrics.slice(1)
  const fallbacks = ['weekIn', 'monthIn', 'totalIn', 'totalOut']
  const keys = rest.length >= 4
    ? rest.slice(0, 4)
    : [...rest, ...fallbacks.filter(k => !rest.includes(k))].slice(0, 4)
  return keys.map(key => ({
    key,
    label: props.getLabel(key),
    value: props.metrics[key] || 0,
  }))
})

const barChartOption = computed(() => ({
  tooltip: {
    backgroundColor: 'rgba(23, 42, 69, 0.9)',
    borderColor: '#1e293b',
    borderRadius: 8,
    textStyle: { color: '#ffffff' },
    formatter(params: any) {
      return `<div style="font-weight:600">${params[0].axisValue}</div>
        <div>进入: ${params[0]?.value || 0}</div>
        <div>出去: ${params[1]?.value || 0}</div>`
    },
  },
  grid: { left: 10, right: 10, top: 10, bottom: 10 },
  xAxis: {
    type: 'category',
    data: props.hourlyData.map(h => h.hour),
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { show: false },
  },
  yAxis: {
    type: 'value',
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { show: false },
    splitLine: { show: false },
  },
  series: [
    {
      type: 'bar',
      barWidth: '40%',
      itemStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: '#60a5fa' },
            { offset: 1, color: '#1e40af' },
          ],
        },
        borderRadius: [3, 3, 0, 0],
      },
      data: props.hourlyData.map(h => h.countIn),
    },
    {
      type: 'bar',
      barWidth: '40%',
      itemStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: '#93c5fd' },
            { offset: 1, color: '#3b82f6' },
          ],
        },
        borderRadius: [3, 3, 0, 0],
      },
      data: props.hourlyData.map(h => h.countOut),
    },
  ],
}))
</script>

<template>
  <div class="relative z-10 h-full flex flex-col p-5">
    <!-- 顶栏 -->
    <div class="flex items-center justify-between mb-4 flex-shrink-0">
      <div class="flex items-center gap-3">
        <img v-if="storeLogo" :src="storeLogo" alt="Logo" class="h-9 w-9 object-contain" />
        <h1 class="text-xl font-bold text-white">{{ config.title }}</h1>
      </div>
      <div class="flex items-center gap-4">
        <span class="text-sm text-[#d1d5db] font-mono">{{ clockTime }}</span>
        <button
          class="w-8 h-8 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-colors cursor-pointer"
          @click="emit('close')"
        >
          <X class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- 指标面板区域：2×2 + 中心 -->
    <div class="flex-1 grid gap-3 min-h-0 mb-3" style="grid-template-columns: 1fr 2fr 1fr; grid-template-rows: 1fr 1fr;">
      <!-- 左上 -->
      <div v-if="cornerMetrics[0]" class="rounded-xl p-4 flex flex-col items-center justify-center" style="background: linear-gradient(135deg, #1e3a5f, #0f2847);">
        <p class="text-sm text-white/80 mb-2">{{ cornerMetrics[0].label }}</p>
        <p class="text-3xl font-bold text-white" style="text-shadow: 0 0 20px rgba(96,165,250,0.5);">{{ loading ? '...' : cornerMetrics[0].value.toLocaleString() }}</p>
      </div>
      <div v-else class="rounded-xl" style="background: linear-gradient(135deg, #1e3a5f, #0f2847);" />

      <!-- 中心大面板 -->
      <div class="rounded-xl p-6 flex flex-col items-center justify-center row-span-2" style="background: linear-gradient(135deg, #1e3a8a, #0f2847);">
        <p class="text-lg text-white/90 mb-3">{{ centerMetric.label }}</p>
        <p class="text-6xl font-bold text-white mb-2" style="text-shadow: 0 0 30px rgba(96,165,250,0.6);">
          {{ loading ? '...' : centerMetric.value.toLocaleString() }}
        </p>
        <button
          class="mt-3 flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-sm text-white transition-colors cursor-pointer"
          style="background: rgba(59,130,246,0.6);"
          @click="$emit('refresh')"
        >
          <RefreshCw class="w-3.5 h-3.5" />
          点击刷新
        </button>
      </div>

      <!-- 右上 -->
      <div v-if="cornerMetrics[1]" class="rounded-xl p-4 flex flex-col items-center justify-center" style="background: linear-gradient(135deg, #1e3a5f, #0f2847);">
        <p class="text-sm text-white/80 mb-2">{{ cornerMetrics[1].label }}</p>
        <p class="text-3xl font-bold text-white" style="text-shadow: 0 0 20px rgba(96,165,250,0.5);">{{ loading ? '...' : cornerMetrics[1].value.toLocaleString() }}</p>
      </div>
      <div v-else class="rounded-xl" style="background: linear-gradient(135deg, #1e3a5f, #0f2847);" />

      <!-- 左下 -->
      <div v-if="cornerMetrics[2]" class="rounded-xl p-4 flex flex-col items-center justify-center" style="background: linear-gradient(135deg, #1e3a5f, #0f2847);">
        <p class="text-sm text-white/80 mb-2">{{ cornerMetrics[2].label }}</p>
        <p class="text-3xl font-bold text-white" style="text-shadow: 0 0 20px rgba(96,165,250,0.5);">{{ loading ? '...' : cornerMetrics[2].value.toLocaleString() }}</p>
      </div>
      <div v-else class="rounded-xl" style="background: linear-gradient(135deg, #1e3a5f, #0f2847);" />

      <!-- 右下 -->
      <div v-if="cornerMetrics[3]" class="rounded-xl p-4 flex flex-col items-center justify-center" style="background: linear-gradient(135deg, #1e3a5f, #0f2847);">
        <p class="text-sm text-white/80 mb-2">{{ cornerMetrics[3].label }}</p>
        <p class="text-3xl font-bold text-white" style="text-shadow: 0 0 20px rgba(96,165,250,0.5);">{{ loading ? '...' : cornerMetrics[3].value.toLocaleString() }}</p>
      </div>
      <div v-else class="rounded-xl" style="background: linear-gradient(135deg, #1e3a5f, #0f2847);" />
    </div>

    <!-- 视频 + 柱状图 一行 -->
    <div class="flex-shrink-0 flex gap-2 mb-3" style="height: 200px;">
      <!-- 实时视频 (1/3) -->
      <div class="w-1/3 grid gap-2" style="grid-template-rows: repeat(auto-fill, 1fr);">
        <div
          v-for="device in devices"
          :key="device.id"
          class="bg-black/40 border border-white/10 rounded-lg overflow-hidden"
        >
          <div class="flex items-center gap-2 px-3 py-1 bg-black/30">
            <Wifi v-if="device.status === 'online'" class="w-3 h-3 text-[#00ff88]" />
            <WifiOff v-else class="w-3 h-3 text-[#ef4444]" />
            <span class="text-xs text-white">{{ device.name }}</span>
          </div>
          <div style="height: calc(100% - 26px);">
            <RTSPVideoPlayer
              :device-id="device.id"
              :name="device.name"
              :status="device.status"
              :auto-play="true"
              :compact="true"
              :show-controls="true"
              class="w-full h-full"
            />
          </div>
        </div>
      </div>

      <!-- 今日客流趋势柱状图 (2/3) -->
      <div class="w-2/3 rounded-xl overflow-hidden" style="background: linear-gradient(135deg, #1e3a5f, #0f2847);">
        <VChart v-if="!loading && hourlyData.length > 0" :option="barChartOption" autoresize style="width: 100%; height: 100%;" />
        <div v-else class="w-full h-full flex items-center justify-center text-[#8892a0] text-sm">
          {{ loading ? '加载中...' : '暂无趋势数据' }}
        </div>
      </div>
    </div>
  </div>
</template>
