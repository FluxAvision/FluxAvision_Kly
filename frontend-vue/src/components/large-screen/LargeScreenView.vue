<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, markRaw } from 'vue'
import {
  X, LogIn, LogOut, Users, TrendingUp, TrendingDown, CalendarDays, Hash, Video, Wifi, WifiOff,
} from 'lucide-vue-next'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import RTSPVideoPlayer from '@/components/video/RTSPVideoPlayer.vue'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent])

const emit = defineEmits<{ close: [] }>()

interface LargeScreenConfig {
  title: string
  subtitle: string
  logo: string
  backgroundImage: string
  metrics: string[]
  deviceIds: string[]
  templateId: string
}

interface HourlyData {
  hour: string
  countIn: number
  countOut: number
}

interface Device {
  id: string
  name: string
  ip: string
  status: string
}

const metricMap: Record<string, { label: string; icon: any; color: string }> = {
  todayIn: { label: '今日进', icon: markRaw(LogIn), color: '#00d9ff' },
  todayOut: { label: '今日出', icon: markRaw(LogOut), color: '#00ff88' },
  currentIn: { label: '当前在场', icon: markRaw(Users), color: '#4a9eff' },
  weekIn: { label: '本周进', icon: markRaw(TrendingUp), color: '#ff9500' },
  weekOut: { label: '本周出', icon: markRaw(TrendingDown), color: '#a855f7' },
  monthIn: { label: '本月进', icon: markRaw(CalendarDays), color: '#f43f5e' },
  monthOut: { label: '本月出', icon: markRaw(CalendarDays), color: '#f97316' },
  totalIn: { label: '累计进', icon: markRaw(Hash), color: '#06b6d4' },
  totalOut: { label: '累计出', icon: markRaw(Hash), color: '#10b981' },
}

const templateGradients: Record<string, string> = {
  'tpl-blue': 'linear-gradient(135deg, #0a192f 0%, #1e3a5f 50%, #0a192f 100%)',
  'tpl-tech': 'linear-gradient(135deg, #0a192f 0%, #0a2540 30%, #0d1b30 60%, #0a192f 100%)',
  'tpl-minimal': 'linear-gradient(135deg, #0a192f 0%, #112240 100%)',
  'tpl-data': 'linear-gradient(135deg, #0a192f 0%, #0f2a1f 50%, #0a192f 100%)',
}

const config = ref<LargeScreenConfig>({
  title: '客流统计大屏',
  subtitle: '实时客流数据展示',
  logo: '',
  backgroundImage: '',
  metrics: ['todayIn', 'todayOut', 'currentIn'],
  deviceIds: [],
  templateId: '',
})

const metrics = ref<Record<string, number>>({
  todayIn: 0, todayOut: 0, currentIn: 0, weekIn: 0, weekOut: 0,
  monthIn: 0, monthOut: 0, totalIn: 0, totalOut: 0,
})

const hourlyData = ref<HourlyData[]>([])
const devices = ref<Device[]>([])
const loading = ref(true)
let interval: ReturnType<typeof setInterval> | null = null

async function fetchData() {
  try {
    const [screenRes, dashRes, devRes] = await Promise.all([
      fetch('/api/large-screen'),
      fetch('/api/traffic/dashboard'),
      fetch('/api/devices'),
    ])

    if (screenRes.ok) {
      const json = await screenRes.json()
      const screenData = json.data || json
      config.value = {
        title: screenData.title || '客流统计大屏',
        subtitle: screenData.subtitle || '实时客流数据展示',
        logo: screenData.logo || '',
        backgroundImage: screenData.backgroundImage || '',
        metrics: screenData.metrics ? screenData.metrics.split(',') : ['todayIn', 'todayOut', 'currentIn'],
        deviceIds: screenData.deviceIds ? screenData.deviceIds.split(',').filter(Boolean) : [],
        templateId: screenData.templateId || '',
      }
    }
    if (dashRes.ok) {
      const json = await dashRes.json()
      const dashData = json.data || json
      const st = dashData.storeTotal || {}
      metrics.value = {
        todayIn: st.todayIn || dashData.todayIn || 0,
        todayOut: st.todayOut || dashData.todayOut || 0,
        currentIn: st.currentIn || dashData.currentIn || 0,
        weekIn: st.weekIn || dashData.weekIn || 0,
        weekOut: st.weekOut || dashData.weekOut || 0,
        monthIn: st.monthIn || dashData.monthIn || 0,
        monthOut: st.monthOut || dashData.monthOut || 0,
        totalIn: st.totalIn || dashData.totalIn || 0,
        totalOut: st.totalOut || dashData.totalOut || 0,
      }
      hourlyData.value = (dashData.hourlyToday || []).map((h: any) => ({
        ...h,
        hour: `${String(h.hour).padStart(2, '0')}:00`,
      }))
    }
    if (devRes.ok) {
      const json = await devRes.json()
      const allDevices: Device[] = Array.isArray(json.data) ? json.data : (Array.isArray(json) ? json : [])
      const effectiveIds = config.value.deviceIds.length > 0
        ? config.value.deviceIds
        : allDevices.filter(d => d.status === 'online').slice(0, 4).map(d => d.id)
      devices.value = allDevices.filter((d) => effectiveIds.includes(d.id))
    }
  } catch {
    // Keep defaults
  } finally {
    loading.value = false
  }
}

const bgStyle = computed(() => {
  if (config.value.backgroundImage) {
    return {
      backgroundImage: `url(${config.value.backgroundImage})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
    }
  }
  return {
    background: templateGradients[config.value.templateId] || templateGradients['tpl-blue'],
  }
})

const chartOption = computed(() => ({
  tooltip: {
    backgroundColor: 'rgba(23, 42, 69, 0.9)',
    borderColor: '#1e293b',
    borderRadius: 8,
    textStyle: { color: '#ffffff' },
  },
  grid: { left: 40, right: 20, top: 10, bottom: 30 },
  xAxis: {
    type: 'category',
    data: hourlyData.value.map(h => h.hour),
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
      data: hourlyData.value.map(h => h.countIn),
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
      data: hourlyData.value.map(h => h.countOut),
    },
  ],
}))

onMounted(() => {
  fetchData()
  interval = setInterval(fetchData, 15000)
})

onUnmounted(() => {
  if (interval) clearInterval(interval)
})
</script>

<template>
  <div class="fixed inset-0 z-[100] overflow-hidden" :style="bgStyle">
    <!-- Overlay for readability -->
    <div class="absolute inset-0 bg-black/30" />

    <!-- Content -->
    <div class="relative z-10 h-full flex flex-col">
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-white/10">
        <div class="flex items-center gap-4">
          <img v-if="config.logo" :src="config.logo" alt="Logo" class="h-10 w-10 object-contain" />
          <div>
            <h1 class="text-2xl font-bold text-white glow-text-cyan">{{ config.title }}</h1>
            <p class="text-sm text-[#8892a0]">{{ config.subtitle }}</p>
          </div>
        </div>
        <button
          class="w-10 h-10 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-colors cursor-pointer"
          @click="emit('close')"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Main Content -->
      <div class="flex-1 flex gap-4 p-4 min-h-0">
        <!-- Left: Metrics -->
        <div class="w-64 flex-shrink-0 flex flex-col gap-4">
          <div
            v-for="key in config.metrics"
            :key="key"
            class="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-5"
          >
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm text-[#8892a0]">{{ metricMap[key]?.label }}</span>
              <component :is="metricMap[key]?.icon" v-if="metricMap[key]" :style="{ color: metricMap[key].color }" class="w-6 h-6" />
            </div>
            <p
              class="text-3xl font-bold animate-count-up"
              :style="{ color: metricMap[key]?.color }"
            >
              {{ loading ? '...' : (metrics[key]?.toLocaleString() || 0) }}
            </p>
          </div>
        </div>

        <!-- Center/Right: Video Grid + Chart -->
        <div class="flex-1 flex flex-col gap-4 min-w-0">
          <!-- Video Grid -->
          <div
            class="flex-1 grid gap-4 min-h-0"
            :style="{
              gridTemplateColumns: devices.length > 1 ? 'repeat(2, 1fr)' : '1fr',
              gridTemplateRows: devices.length > 2 ? 'repeat(2, 1fr)' : '1fr',
            }"
          >
            <div v-if="devices.length === 0 && !loading" class="col-span-2 flex items-center justify-center text-[#8892a0]">
              <div class="text-center">
                <Video class="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p class="text-sm">暂无视频设备</p>
              </div>
            </div>
            <div
              v-for="device in devices"
              :key="device.id"
              class="bg-black/40 border border-white/10 rounded-lg flex flex-col overflow-hidden"
            >
              <div class="flex items-center justify-between px-3 py-2 bg-black/30 flex-shrink-0">
                <div class="flex items-center gap-2">
                  <Wifi v-if="device.status === 'online'" class="w-3.5 h-3.5 text-[#00ff88]" />
                  <WifiOff v-else class="w-3.5 h-3.5 text-[#ef4444]" />
                  <span class="text-xs text-white">{{ device.name }}</span>
                </div>
                <span class="text-xs text-[#8892a0] font-mono">{{ device.ip }}</span>
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

          <!-- Bottom Chart -->
          <div class="h-48 flex-shrink-0 bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-4">
            <h3 class="text-sm text-[#8892a0] mb-2">今日客流趋势</h3>
            <VChart :option="chartOption" autoresize style="width: 100%; height: 80px;" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
