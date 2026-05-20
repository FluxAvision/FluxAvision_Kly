<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, markRaw, type Component } from 'vue'
import {
  LogIn, LogOut, Users, TrendingUp, TrendingDown, Camera, CalendarDays, Hash, Store,
} from 'lucide-vue-next'
import RTSPVideoPlayer from '../video/RTSPVideoPlayer.vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

interface HourlyData {
  hour: number
  countIn: number
  countOut: number
}

interface DeviceTodayData {
  deviceId: string
  deviceName: string
  deviceIp: string
  deviceLocation: string
  deviceStatus: string
  todayIn: number
  todayOut: number
  currentInside: number
  percentage: number
}

interface DeviceStatus {
  id: string
  name: string
  location: string
  status: string
  ip: string
  model: string
}

interface DashboardApiData {
  storeName: string
  storeTotal: {
    todayIn: number
    todayOut: number
    currentIn: number
    weekIn: number
    weekOut: number
    monthIn: number
    monthOut: number
    totalIn: number
    totalOut: number
  }
  devicesToday: DeviceTodayData[]
  hourlyToday: HourlyData[]
  peakHour: number | null
  devices: DeviceStatus[]
}

interface MetricConfigItem {
  label: string
  icon: Component
  bgColor: string
}

const props = defineProps<{
  dashboardMetrics?: string
  dashboardMetricsLabels?: string
}>()

const metricConfig: Record<string, MetricConfigItem> = {
  todayIn: { label: '今日进', icon: markRaw(LogIn), bgColor: 'rgba(0, 217, 255, 0.1)' },
  todayOut: { label: '今日出', icon: markRaw(LogOut), bgColor: 'rgba(0, 255, 136, 0.1)' },
  currentIn: { label: '当前在场', icon: markRaw(Users), bgColor: 'rgba(74, 158, 255, 0.1)' },
  weekIn: { label: '本周进', icon: markRaw(TrendingUp), bgColor: 'rgba(255, 149, 0, 0.1)' },
  weekOut: { label: '本周出', icon: markRaw(TrendingDown), bgColor: 'rgba(168, 85, 247, 0.1)' },
  monthIn: { label: '本月进', icon: markRaw(CalendarDays), bgColor: 'rgba(244, 63, 94, 0.1)' },
  monthOut: { label: '本月出', icon: markRaw(CalendarDays), bgColor: 'rgba(249, 115, 22, 0.1)' },
  totalIn: { label: '累计进人数', icon: markRaw(Hash), bgColor: 'rgba(6, 182, 212, 0.1)' },
  totalOut: { label: '累计出人数', icon: markRaw(Hash), bgColor: 'rgba(16, 185, 129, 0.1)' },
}

const defaultHourlyData = Array.from({ length: 24 }, (_, i) => ({
  hour: i,
  countIn: 0,
  countOut: 0,
}))

const DEVICE_COLORS = ['#00d9ff', '#00ff88', '#ff9500', '#a855f7', '#f43f5e', '#06b6d4', '#f97316', '#10b981']

const data = ref<DashboardApiData | null>(null)
const loading = ref(true)

let interval: ReturnType<typeof setInterval> | null = null

async function fetchData() {
  try {
    const res = await fetch('/api/traffic/dashboard')
    if (res.ok) {
      const json = await res.json()
      const apiData: DashboardApiData = json.data || json
      console.log('[Dashboard] hourlyToday data:', apiData.hourlyToday?.slice(0, 5))
      data.value = apiData
    }
  } catch (e) {
    console.error('[Dashboard] fetch error:', e)
    // Keep null
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
  interval = setInterval(fetchData, 30000)
})

onUnmounted(() => {
  if (interval) clearInterval(interval)
})

const storeName = computed(() => data.value?.storeName || '我的门店')
const storeTotal = computed(() => data.value?.storeTotal)
const metrics = computed(() => props.dashboardMetrics ? props.dashboardMetrics.split(',') : ['todayIn', 'todayOut', 'currentIn', 'weekIn'])
const customLabels = computed(() => {
  if (!props.dashboardMetricsLabels) return {}
  try { return JSON.parse(props.dashboardMetricsLabels) } catch { return {} }
})
function getLabel(key: string): string {
  return customLabels.value[key] || metricConfig[key]?.label || key
}
const hourlyData = computed(() => {
  const source = data.value?.hourlyToday || defaultHourlyData
  return source.map((h, index) => ({
    hour: `${String(h.hour ?? index).padStart(2, '0')}:00`,
    countIn: h.countIn ?? 0,
    countOut: h.countOut ?? 0,
  }))
})
const devices = computed(() => data.value?.devices || [])
const devicesToday = computed(() => data.value?.devicesToday || [])
const peakHour = computed(() => data.value?.peakHour)

// 实时视频设备切换
const selectedVideoDeviceId = ref<string>('')
const selectedVideoDevice = computed(() => devices.value.find(d => d.id === selectedVideoDeviceId.value))

watch(devices, (list) => {
  if (list.length > 0 && !selectedVideoDeviceId.value) {
    selectedVideoDeviceId.value = list[0].id
  }
}, { immediate: true })

const hourlyChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis' as const,
    backgroundColor: '#172a45',
    borderColor: '#1e293b',
    borderWidth: 1,
    borderRadius: 8,
    textStyle: { color: '#ffffff' },
    formatter(params: any[]) {
      if (!Array.isArray(params)) return ''
      let html = `<div style="font-size:12px;margin-bottom:4px;color:#8892a0">${params[0]?.axisValueLabel}</div>`
      params.forEach((p: any) => {
        const label = p.seriesName === 'countIn' ? '进人数' : '出人数'
        html += `<div style="display:flex;align-items:center;gap:6px;margin:2px 0">
          <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${p.color}"></span>
          <span style="color:#8892a0">${label}</span>
          <span style="color:#fff;font-weight:500;margin-left:auto">${Number(p.value).toLocaleString()}</span>
        </div>`
      })
      return html
    },
  },
  legend: {
    data: ['countIn', 'countOut'],
    top: 5,
    formatter(name: string) {
      return name === 'countIn' ? '进人数' : '出人数'
    },
    textStyle: { color: '#8892a0' },
  },
  grid: {
    left: 40,
    right: 20,
    top: 40,
    bottom: 35,
  },
  xAxis: {
    type: 'category' as const,
    data: hourlyData.value.map(h => h.hour),
    axisLine: { lineStyle: { color: '#8892a0' } },
    axisTick: { show: false },
    axisLabel: {
      color: '#8892a0',
      fontSize: 11,
      interval: 0,
      rotate: 45,
    },
    boundaryGap: false,
  },
  yAxis: {
    type: 'value' as const,
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: '#8892a0', fontSize: 12 },
    splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' as const } },
  },
  series: [
    {
      name: 'countIn',
      type: 'line',
      smooth: true,
      symbol: 'none',
      lineStyle: { color: '#00d9ff', width: 2 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0.05, color: 'rgba(0, 217, 255, 0.3)' },
            { offset: 0.95, color: 'rgba(0, 217, 255, 0)' },
          ],
        },
      },
      data: hourlyData.value.map(h => h.countIn),
    },
    {
      name: 'countOut',
      type: 'line',
      smooth: true,
      symbol: 'none',
      lineStyle: { color: '#00ff88', width: 2 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0.05, color: 'rgba(0, 255, 136, 0.3)' },
            { offset: 0.95, color: 'rgba(0, 255, 136, 0)' },
          ],
        },
      },
      data: hourlyData.value.map(h => h.countOut),
    },
  ],
}))

function getMetricValue(key: string): number {
  if (!storeTotal.value) return 0
  return (storeTotal.value as any)[key] || 0
}
</script>

<template>
  <div class="space-y-6">
    <!-- 门店名称 + 指标卡片 -->
    <div>
      <div class="flex items-center gap-2 mb-4">
        <Store class="w-4 h-4 text-[#00d9ff]" />
        <h2 class="text-lg font-medium text-white">{{ storeName }}</h2>
        <span class="text-xs text-[#8892a0]">· 门店汇总</span>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <template v-for="key in metrics" :key="key">
          <div v-if="metricConfig[key]" class="metric-card p-5">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-[#8892a0] mb-1">{{ getLabel(key) }}</p>
                <a-skeleton v-if="loading" class="h-8 w-24" :loading="true" :paragraph="false" />
                <p v-else class="text-2xl font-bold text-white animate-count-up">
                  {{ getMetricValue(key).toLocaleString() }}
                </p>
              </div>
              <div
                class="w-10 h-10 rounded-lg flex items-center justify-center"
                :style="{ backgroundColor: metricConfig[key].bgColor }"
              >
                <component :is="metricConfig[key].icon" class="w-5 h-5" />
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- 今日客流趋势 + 实时视频 并排一行 -->
    <div class="flex flex-col lg:flex-row gap-4">
      <!-- 今日客流趋势 (2/3) -->
      <div class="flex-[2] bg-[#112240] border border-[#1e293b] rounded-lg p-5">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-white font-medium">今日客流趋势</h3>
          <span v-if="peakHour !== null && peakHour !== undefined" class="text-xs text-[#8892a0]">
            高峰时段: <span class="text-[#ff9500] font-medium">{{ String(peakHour).padStart(2, '0') }}:00</span>
          </span>
        </div>
        <a-skeleton v-if="loading" class="h-[300px] w-full" :loading="true" :paragraph="false" />
        <VChart v-else :option="hourlyChartOption" class="w-full" style="height: 300px" autoresize />
      </div>

      <!-- 实时视频 (1/3) -->
      <div class="flex-1 bg-[#112240] border border-[#1e293b] rounded-lg p-5">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-white font-medium">实时视频</h3>
        </div>
        <template v-if="loading">
          <a-skeleton class="h-[200px] w-full" :loading="true" :paragraph="false" />
        </template>
        <template v-else-if="devices.length === 0">
          <div class="text-center py-12 text-[#8892a0]">
            <Camera class="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p class="text-sm mb-1">暂无设备</p>
            <p class="text-xs opacity-60">请前往「设备管理」页面添加摄像头设备</p>
          </div>
        </template>
        <template v-else>
          <!-- 设备切换下拉 -->
          <div class="mb-3">
            <a-select
              v-model:value="selectedVideoDeviceId"
              style="width: 100%"
              placeholder="选择设备"
              :options="devices.map(d => ({ value: d.id, label: d.name }))"
              size="small"
              variant="borderless"
              :popup-style="{ background: '#112240', border: '1px solid #1e293b' }"
            >
              <template #suffixIcon>
                <Camera class="w-3.5 h-3.5 text-[#00d9ff]" />
              </template>
            </a-select>
          </div>
          <!-- 视频播放器 -->
          <div class="rounded-lg overflow-hidden">
            <RTSPVideoPlayer
              v-if="selectedVideoDeviceId"
              :key="selectedVideoDeviceId"
              :device-id="selectedVideoDeviceId"
              :name="selectedVideoDevice?.name || ''"
              :status="selectedVideoDevice?.status || 'offline'"
              compact
              class="w-full"
              style="min-height: 180px"
            />
            <div v-else class="h-[180px] flex items-center justify-center bg-black/40 rounded-lg">
              <p class="text-xs text-[#8892a0]">请选择设备</p>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- 各设备今日客流 + 设备状态 并排一行 -->
    <div class="flex flex-col lg:flex-row gap-4">
      <!-- 各设备今日客流分栏明细 -->
      <div v-if="devicesToday.length > 0" class="flex-1 bg-[#112240] border border-[#1e293b] rounded-lg p-5">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <h3 class="text-white font-medium">各设备今日客流</h3>
            <span class="text-xs text-[#8892a0]">门店客流由 {{ devicesToday.length }} 台设备汇总得出</span>
          </div>
        </div>
        <template v-if="loading">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <a-skeleton v-for="i in 2" :key="i" class="h-24 w-full rounded-lg" :loading="true" :paragraph="false" />
          </div>
        </template>
        <template v-else>
          <!-- 设备卡片列表 -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
            <div
              v-for="(dev, idx) in devicesToday"
              :key="dev.deviceId"
              class="bg-[#0a192f] border border-[#1e293b] rounded-lg p-4 card-hover"
            >
              <div class="flex items-center justify-between mb-3">
                <div class="flex items-center gap-2">
                  <div
                    class="w-2.5 h-2.5 rounded-full"
                    :style="{ backgroundColor: DEVICE_COLORS[idx % DEVICE_COLORS.length] }"
                  />
                  <span class="text-sm text-white font-medium truncate">
                    {{ dev.deviceName }}
                  </span>
                </div>
                <span class="text-xs text-[#8892a0]">
                  占比 {{ dev.percentage }}%
                </span>
              </div>
              <div class="flex items-center gap-3">
                <div class="flex-1">
                  <div class="flex items-baseline gap-1">
                    <span class="text-lg font-bold text-[#00d9ff]">
                      {{ dev.todayIn.toLocaleString() }}
                    </span>
                    <span class="text-[10px] text-[#8892a0]">进</span>
                  </div>
                  <div class="flex items-baseline gap-1 mt-0.5">
                    <span class="text-sm text-[#00ff88]">
                      {{ dev.todayOut.toLocaleString() }}
                    </span>
                    <span class="text-[10px] text-[#8892a0]">出</span>
                  </div>
                </div>
                <div class="text-right">
                  <p class="text-[10px] text-[#8892a0]">在场</p>
                  <p class="text-sm font-medium text-[#4a9eff]">
                    {{ dev.currentInside }}
                  </p>
                </div>
              </div>
              <!-- 占比进度条 -->
              <div class="mt-2 h-1.5 bg-[#1e293b] rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-500"
                  :style="{
                    width: `${dev.percentage}%`,
                    backgroundColor: DEVICE_COLORS[idx % DEVICE_COLORS.length],
                  }"
                />
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- 设备在线状态 -->
      <div class="flex-1 bg-[#112240] border border-[#1e293b] rounded-lg p-5">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-white font-medium">设备状态</h3>
          <span class="text-xs text-[#8892a0]">
            共 {{ devices.length }} 台设备 · 在线 {{ devices.filter(d => d.status === 'online').length }} 台
          </span>
        </div>
        <template v-if="loading">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <a-skeleton v-for="i in 2" :key="i" class="h-20 w-full rounded-lg" :loading="true" :paragraph="false" />
          </div>
        </template>
        <div v-else-if="devices.length === 0" class="text-center py-12 text-[#8892a0]">
          <Camera class="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p class="text-sm mb-1">暂无设备</p>
          <p class="text-xs opacity-60">请前往「设备管理」页面添加摄像头设备</p>
        </div>
        <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div
            v-for="device in devices"
            :key="device.id"
            class="flex items-center gap-3 bg-[#0a192f] border border-[#1e293b] rounded-lg p-4 card-hover"
          >
            <div
              class="w-10 h-10 rounded-lg flex items-center justify-center"
              :class="{
                'bg-[#00ff88]/10': device.status === 'online',
                'bg-[#ff9500]/10': device.status === 'warning',
                'bg-[#ef4444]/10': device.status !== 'online' && device.status !== 'warning',
              }"
            >
              <Camera
                class="w-5 h-5 flex-shrink-0"
                :class="{
                  'text-[#00ff88]': device.status === 'online',
                  'text-[#ff9500]': device.status === 'warning',
                  'text-[#ef4444]': device.status !== 'online' && device.status !== 'warning',
                }"
              />
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm text-white font-medium truncate">
                {{ device.name }}
              </p>
              <p class="text-xs text-[#8892a0] truncate">
                {{ device.location }} · {{ device.ip }}
              </p>
            </div>
            <div class="flex items-center gap-1.5 flex-shrink-0">
              <div
                class="w-2 h-2 rounded-full"
                :class="{
                  'bg-[#00ff88] animate-pulse-green': device.status === 'online',
                  'bg-[#ff9500]': device.status === 'warning',
                  'bg-[#ef4444]': device.status !== 'online' && device.status !== 'warning',
                }"
              />
              <span
                class="text-xs font-medium"
                :class="{
                  'text-[#00ff88]': device.status === 'online',
                  'text-[#ff9500]': device.status === 'warning',
                  'text-[#ef4444]': device.status !== 'online' && device.status !== 'warning',
                }"
              >
                {{ device.status === 'online' ? '在线' : device.status === 'warning' ? '告警' : '离线' }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
