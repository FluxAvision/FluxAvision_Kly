<script setup lang="ts">
import { computed } from 'vue'
import { X, Video, Wifi, WifiOff } from 'lucide-vue-next'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import RTSPVideoPlayer from '@/components/video/RTSPVideoPlayer.vue'
import { metricMap } from '../composables/useLargeScreenData'
import type { HourlyData, Device, LargeScreenConfig } from '../composables/useLargeScreenData'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent])

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

// 人物图标映射
const personIcons: Record<string, number> = {
  todayIn: 1, todayOut: 1,
  currentIn: 2, weekIn: 2, weekOut: 2,
  monthIn: 3, monthOut: 3, totalIn: 3, totalOut: 3,
}

const totalInDigits = computed(() => {
  const val = String(props.metrics.totalIn || 0).padStart(8, '0')
  return val.split('')
})

const generalCards = computed(() =>
  props.config.metrics.slice(0, 3).map(key => ({
    key,
    label: props.getLabel(key),
    value: props.metrics[key] || 0,
    color: metricMap[key]?.color || '#00d9ff',
    personCount: personIcons[key] || 1,
  }))
)

const lineChartOption = computed(() => ({
  tooltip: {
    backgroundColor: 'rgba(23, 42, 69, 0.9)',
    borderColor: '#1e293b',
    borderRadius: 8,
    textStyle: { color: '#ffffff' },
  },
  grid: { left: 40, right: 20, top: 10, bottom: 30 },
  xAxis: {
    type: 'category',
    data: props.hourlyData.map(h => h.hour),
    axisLine: { lineStyle: { color: '#1e293b' } },
    axisLabel: { color: '#8892a0', fontSize: 10 },
    interval: 3,
  },
  yAxis: {
    type: 'value',
    axisLine: { lineStyle: { color: '#1e293b' } },
    axisLabel: { color: '#8892a0', fontSize: 10 },
    splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } },
  },
  series: [
    {
      type: 'line',
      smooth: true,
      symbol: 'none',
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0.05, color: 'rgba(0, 217, 255, 0.3)' },
            { offset: 0.95, color: 'rgba(0, 217, 255, 0)' },
          ],
        },
      },
      lineStyle: { color: '#00d9ff', width: 2 },
      itemStyle: { color: '#00d9ff' },
      data: props.hourlyData.map(h => h.countIn),
    },
    {
      type: 'line',
      smooth: true,
      symbol: 'none',
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0.05, color: 'rgba(0, 255, 136, 0.3)' },
            { offset: 0.95, color: 'rgba(0, 255, 136, 0)' },
          ],
        },
      },
      lineStyle: { color: '#00ff88', width: 2 },
      itemStyle: { color: '#00ff88' },
      data: props.hourlyData.map(h => h.countOut),
    },
  ],
}))
</script>

<template>
  <div class="relative z-10 h-full flex flex-col px-6 py-4">
    <!-- 装饰点阵背景 -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute bottom-0 right-0 w-2/3 h-1/3" style="background-image: radial-gradient(circle, rgba(74,158,255,0.15) 1px, transparent 1px); background-size: 24px 24px;" />
      <div class="absolute top-0 left-0 w-1/3 h-1/4" style="background-image: radial-gradient(circle, rgba(74,158,255,0.08) 1px, transparent 1px); background-size: 24px 24px;" />
    </div>

    <!-- 顶栏 -->
    <div class="relative z-10 w-full flex items-center justify-between mb-4 flex-shrink-0">
      <div class="flex items-center gap-3">
        <img v-if="storeLogo" :src="storeLogo" alt="Logo" class="h-10 w-10 object-contain" />
        <div>
          <h1 class="text-xl font-bold text-white glow-text-cyan">{{ config.title }}</h1>
          <p class="text-xs text-[#8892a0]">{{ config.subtitle }}</p>
        </div>
      </div>
      <div class="flex items-center gap-4">
        <span class="text-[28px] text-[#d1d5db] font-mono">{{ clockTime }}</span>
        <button
          class="w-9 h-9 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-colors cursor-pointer"
          @click="emit('close')"
        >
          <X class="w-5 h-5" />
        </button>
      </div>
    </div>

    <!-- 主体内容 -->
    <div class="relative z-10 w-full flex-1 flex flex-col min-h-0">
      <!-- 上半区：胶囊 + 计数器 + 卡片 -->
      <div class="flex-shrink-0 flex flex-col items-center mb-4">
        <!-- 胶囊标题 -->
        <div class="mb-4 px-6 py-2 rounded-full" style="background: rgba(74,158,255,0.1); border: 1px solid rgba(74,158,255,0.3);">
          <span class="text-base text-white font-medium">来访总人数</span>
        </div>

        <!-- 8位数字计数器 -->
        <div class="flex items-center gap-2 mb-4">
          <div
            v-for="(digit, idx) in totalInDigits"
            :key="idx"
            class="w-12 h-16 flex items-center justify-center rounded-lg text-3xl font-bold text-white"
            style="background: rgba(10,26,58,0.8); border: 1px solid rgba(74,158,255,0.4); box-shadow: inset 0 2px 8px rgba(0,0,0,0.3), 0 0 10px rgba(74,158,255,0.1);"
          >
            {{ loading ? '' : digit }}
          </div>
        </div>

        <!-- 3张指标卡片 -->
        <div class="grid grid-cols-3 gap-4 w-full">
          <div
            v-for="card in generalCards"
            :key="card.key"
            class="rounded-xl overflow-hidden"
            style="background: rgba(10,30,60,0.7); border: 1px solid rgba(74,158,255,0.25);"
          >
            <!-- 装饰箭头顶栏 -->
            <div class="h-7 flex items-center justify-between px-3" style="background: linear-gradient(90deg, rgba(74,158,255,0.3), rgba(74,158,255,0.1), rgba(74,158,255,0.3));">
              <div class="flex gap-0.5">
                <span class="text-white/50 text-xs">&gt;&gt;&gt;</span>
              </div>
              <span class="text-lg text-white/70 font-medium">{{ card.label }}</span>
              <div class="flex gap-0.5">
                <span class="text-white/50 text-xs">&lt;&lt;&lt;</span>
              </div>
            </div>
            <!-- 内容 -->
            <div class="flex flex-col items-center py-4">
              <!-- 人物图标 -->
              <svg class="w-10 h-10 mb-2 text-white/70" viewBox="0 0 24 24" fill="currentColor">
                <circle cx="12" cy="5" r="3" />
                <path v-if="card.personCount === 1" d="M6 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" fill="none" stroke="currentColor" stroke-width="1.5" />
                <g v-else-if="card.personCount === 2">
                  <path d="M4 21v-2a3 3 0 0 1 3-3h0" fill="none" stroke="currentColor" stroke-width="1.5" />
                  <circle cx="7" cy="7" r="2.5" />
                  <path d="M20 21v-2a3 3 0 0 0-3-3h0" fill="none" stroke="currentColor" stroke-width="1.5" />
                  <circle cx="17" cy="7" r="2.5" />
                </g>
                <g v-else>
                  <path d="M3 21v-2a3 3 0 0 1 3-3h0" fill="none" stroke="currentColor" stroke-width="1.5" />
                  <circle cx="6" cy="7" r="2" />
                  <circle cx="12" cy="5" r="2.5" />
                  <path d="M9 21v-2a3 3 0 0 1 3-3h0" fill="none" stroke="currentColor" stroke-width="1.5" />
                  <path d="M21 21v-2a3 3 0 0 0-3-3h0" fill="none" stroke="currentColor" stroke-width="1.5" />
                  <circle cx="18" cy="7" r="2" />
                </g>
              </svg>
              <p class="text-4xl font-bold text-white">{{ loading ? '...' : card.value.toLocaleString() }}</p>
              <p class="text-sm text-white/50 mt-1">人</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 视频 + 趋势图 一行（弹性填充） -->
      <div class="flex-1 flex gap-3 w-full min-h-0">
        <!-- 实时视频 (1/3) -->
        <div v-if="devices.length > 0" class="w-1/3 grid gap-2" style="grid-template-rows: repeat(auto-fill, 1fr);">
          <div
            v-for="device in devices.slice(0, 4)"
            :key="device.id"
            class="bg-black/40 border border-white/10 rounded-lg overflow-hidden flex flex-col"
          >
            <div class="flex items-center gap-1.5 px-2 py-1 bg-black/30 flex-shrink-0">
              <Wifi v-if="device.status === 'online'" class="w-3 h-3 text-[#00ff88]" />
              <WifiOff v-else class="w-3 h-3 text-[#ef4444]" />
              <span class="text-[11px] text-white truncate">{{ device.name }}</span>
            </div>
            <div class="flex-1 min-h-0">
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
        <div v-else-if="!loading" class="w-1/3 flex items-center justify-center text-[#8892a0]">
          <div class="text-center">
            <Video class="w-8 h-8 mx-auto mb-1 opacity-50" />
            <p class="text-xs">暂无视频设备</p>
          </div>
        </div>
        <div v-else class="w-1/3 flex items-center justify-center text-[#8892a0] text-sm">加载中...</div>

        <!-- 今日客流趋势 (2/3) -->
        <div class="w-2/3 rounded-lg p-4 flex flex-col" style="background: rgba(10,30,60,0.5); border: 1px solid rgba(74,158,255,0.15);">
          <h3 class="text-sm text-[#8892a0] mb-2 flex-shrink-0">今日客流趋势</h3>
          <div class="flex-1 min-h-0">
            <VChart v-if="!loading && hourlyData.length > 0" :option="lineChartOption" autoresize style="width: 100%; height: 100%;" />
            <div v-else class="w-full h-full flex items-center justify-center text-[#8892a0] text-sm">
              {{ loading ? '加载中...' : '暂无趋势数据' }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部装饰点阵 -->
    <div class="relative z-10 flex-shrink-0 flex justify-center gap-3 py-2 pointer-events-none">
      <span v-for="i in 20" :key="i" class="w-1.5 h-1.5 rounded-full" style="background: rgba(74,158,255,0.25);" />
    </div>
  </div>
</template>

<style scoped>
.glow-text-cyan {
  text-shadow: 0 0 10px rgba(0, 217, 255, 0.4);
}
</style>
