<template>
  <div class="space-y-4">
    <!-- Toolbar -->
    <div class="bg-[#112240] border border-[#1e293b] rounded-lg p-4">
      <div class="flex items-center gap-4 flex-wrap">
        <div class="flex items-center gap-2">
          <label class="text-sm text-[#8892a0]">开始日期</label>
          <a-date-picker
            :value="startDate ? dayjs(startDate) : null"
            @change="(_d: any, dateStr: string) => startDate = dateStr"
            class="history-date-picker"
            placeholder=""
          />
        </div>
        <div class="flex items-center gap-2">
          <label class="text-sm text-[#8892a0]">结束日期</label>
          <a-date-picker
            :value="endDate ? dayjs(endDate) : null"
            @change="(_d: any, dateStr: string) => endDate = dateStr"
            class="history-date-picker"
            placeholder=""
          />
        </div>
        <div class="flex items-center gap-2">
          <label class="text-sm text-[#8892a0]">设备筛选</label>
          <a-select
            :value="selectedDevice"
            @change="selectedDevice = $event"
            class="w-44"
            popup-class-name="device-select-dropdown"
          >
            <a-select-option value="__all__">门店汇总 (全部设备)</a-select-option>
            <a-select-option
              v-for="d in deviceOptions"
              :key="d.id"
              :value="d.id"
            >
              {{ d.name }}
            </a-select-option>
          </a-select>
        </div>
        <button
          @click="fetchData"
          :disabled="loading"
          class="bg-[#00d9ff] text-[#0a192f] rounded-md px-4 py-2 text-xs font-medium transition-colors flex items-center gap-2 hover:bg-[#00d9ff]/80 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
          查询
        </button>
        <div class="flex border border-[#1e293b] rounded-lg overflow-hidden">
          <button
            @click="chartType = 'area'"
            :class="[
              'flex items-center gap-1.5 px-3 py-2 text-xs font-medium transition-colors cursor-pointer',
              chartType === 'area'
                ? 'bg-[#00d9ff] text-[#0a192f]'
                : 'bg-[#0a192f] text-[#8892a0] hover:text-white',
            ]"
          >
            <LineChart class="w-3.5 h-3.5" />
            趋势图
          </button>
          <button
            @click="chartType = 'bar'"
            :class="[
              'flex items-center gap-1.5 px-3 py-2 text-xs font-medium transition-colors cursor-pointer',
              chartType === 'bar'
                ? 'bg-[#00d9ff] text-[#0a192f]'
                : 'bg-[#0a192f] text-[#8892a0] hover:text-white',
            ]"
          >
            <BarChart3 class="w-3.5 h-3.5" />
            柱状图
          </button>
        </div>
        <button
          @click="handleExportCSV"
          :disabled="data.length === 0 || loading"
          class="border border-[#1e293b] text-[#8892a0] hover:text-white hover:bg-[#172a45] rounded-md px-4 py-2 text-xs font-medium transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Download class="w-4 h-4" />
          导出CSV
        </button>
      </div>
      <!-- 视图说明 -->
      <div class="mt-2">
        <span class="text-xs text-[#8892a0]">
          {{
            isStoreView
              ? '当前查看: 门店汇总 (所有设备客流之和)'
              : `当前查看: 单设备 (${deviceOptions.find(d => d.id === selectedDevice)?.name || ''})`
          }}
        </span>
      </div>
    </div>

    <!-- Chart -->
    <div class="bg-[#112240] border border-[#1e293b] rounded-lg p-5">
      <h3 class="text-white font-medium mb-4">
        历史客流数据 {{ isStoreView ? '(门店汇总)' : '(单设备)' }}
      </h3>
      <div v-if="loading" class="h-[350px] w-full bg-[#1e293b] rounded-md animate-pulse" />
      <div v-else-if="data.length === 0" class="flex items-center justify-center h-[350px] text-[#8892a0]">
        暂无数据
      </div>
      <v-chart v-else :option="chartOption" autoresize class="w-full" style="height: 350px" />
    </div>

    <!-- 单天门店汇总: 各设备分栏明细 -->
    <div
      v-if="!loading && isSingleDay && isStoreView && deviceDailyData.length > 0"
      class="bg-[#112240] border border-[#1e293b] rounded-lg p-5"
    >
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-white font-medium">各设备客流分栏</h3>
        <span class="text-xs text-[#8892a0]">
          {{ deviceDailyData.length }} 台设备贡献
        </span>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        <div
          v-for="(dev, idx) in deviceDailyData"
          :key="dev.deviceId"
          class="bg-[#0a192f] border border-[#1e293b] rounded-lg p-4"
        >
          <div class="flex items-center gap-2 mb-3">
            <Camera class="w-4 h-4" :style="{ color: DEVICE_COLORS[idx % DEVICE_COLORS.length] }" />
            <span class="text-sm text-white font-medium truncate">{{ dev.deviceName }}</span>
            <span class="text-xs text-[#8892a0] ml-auto">{{ dev.percentage }}%</span>
          </div>
          <div class="grid grid-cols-3 gap-2">
            <div>
              <p class="text-[10px] text-[#8892a0]">进入</p>
              <p class="text-sm font-bold text-[#00d9ff]">{{ dev.countIn }}</p>
            </div>
            <div>
              <p class="text-[10px] text-[#8892a0]">出去</p>
              <p class="text-sm font-bold text-[#00ff88]">{{ dev.countOut }}</p>
            </div>
            <div>
              <p class="text-[10px] text-[#8892a0]">在场</p>
              <p class="text-sm font-bold text-[#4a9eff]">{{ dev.currentInside }}</p>
            </div>
          </div>
          <div class="mt-2 h-1.5 bg-[#1e293b] rounded-full overflow-hidden">
            <div
              class="h-full rounded-full"
              :style="{
                width: `${dev.percentage}%`,
                backgroundColor: DEVICE_COLORS[idx % DEVICE_COLORS.length],
              }"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Data Table Summary -->
    <div v-if="!loading && data.length > 0" class="bg-[#112240] border border-[#1e293b] rounded-lg p-5">
      <h3 class="text-white font-medium mb-3">
        数据汇总 {{ isStoreView ? '(门店)' : '(单设备)' }}
      </h3>
      <div class="grid grid-cols-3 gap-4">
        <div class="bg-[#0a192f] border border-[#1e293b] rounded-lg p-4 text-center">
          <p class="text-xs text-[#8892a0] mb-1">总进入</p>
          <p class="text-xl font-bold text-[#00d9ff]">
            {{ totalIn.toLocaleString() }}
          </p>
        </div>
        <div class="bg-[#0a192f] border border-[#1e293b] rounded-lg p-4 text-center">
          <p class="text-xs text-[#8892a0] mb-1">总出去</p>
          <p class="text-xl font-bold text-[#00ff88]">
            {{ totalOut.toLocaleString() }}
          </p>
        </div>
        <div class="bg-[#0a192f] border border-[#1e293b] rounded-lg p-4 text-center">
          <p class="text-xs text-[#8892a0] mb-1">日均进入</p>
          <p class="text-xl font-bold text-[#4a9eff]">
            {{ dailyAvgIn.toLocaleString() }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Download, BarChart3, LineChart, Camera } from 'lucide-vue-next'
import dayjs from 'dayjs'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart as ELineChart, BarChart as EBarChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'

use([CanvasRenderer, ELineChart, EBarChart, GridComponent, TooltipComponent, LegendComponent])

interface DailyData {
  date: string
  countIn: number
  countOut: number
}

interface DeviceDailyData {
  deviceId: string
  deviceName: string
  deviceLocation: string
  deviceStatus: string
  deviceIp: string
  countIn: number
  countOut: number
  currentInside: number
  percentage: number
}

interface DeviceOption {
  id: string
  name: string
}

const DEVICE_COLORS = ['#00d9ff', '#00ff88', '#ff9500', '#a855f7', '#f43f5e', '#06b6d4', '#f97316', '#10b981']

const today = new Date()
const defaultEndDate = today.toISOString().split('T')[0]
const weekAgo = new Date(today)
weekAgo.setDate(weekAgo.getDate() - 7)
const defaultStartDate = weekAgo.toISOString().split('T')[0]

const startDate = ref(defaultStartDate)
const endDate = ref(defaultEndDate)
const selectedDevice = ref('__all__')
const deviceOptions = ref<DeviceOption[]>([])
const data = ref<DailyData[]>([])
const deviceDailyData = ref<DeviceDailyData[]>([])
const loading = ref(false)
const chartType = ref<'area' | 'bar'>('area')

const isSingleDay = computed(() => startDate.value === endDate.value)
const isStoreView = computed(() => selectedDevice.value === '__all__')

const chartData = computed(() =>
  data.value.map((d) => ({
    ...d,
    date: d.date.slice(5),
  }))
)

const totalIn = computed(() => data.value.reduce((s, d) => s + d.countIn, 0))
const totalOut = computed(() => data.value.reduce((s, d) => s + d.countOut, 0))
const dailyAvgIn = computed(() => Math.round(totalIn.value / data.value.length))

const chartOption = computed(() => {
  const xData = chartData.value.map((d) => d.date)
  const inData = chartData.value.map((d) => d.countIn)
  const outData = chartData.value.map((d) => d.countOut)

  const isArea = chartType.value === 'area'

  return {
    tooltip: {
      trigger: 'axis' as const,
      backgroundColor: '#172a45',
      borderColor: '#1e293b',
      borderWidth: 1,
      textStyle: { color: '#ffffff', fontSize: 12 },
      formatter(params: any[]) {
        let tip = `<div style="font-weight:600;margin-bottom:4px">${params[0].axisValue}</div>`
        params.forEach((p: any) => {
          const label = p.seriesName === 'countIn' ? '进入' : '出去'
          tip += `<div style="display:flex;align-items:center;gap:4px;margin-top:2px">
            <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${p.color}"></span>
            ${label}: ${p.value.toLocaleString()}
          </div>`
        })
        return tip
      },
    },
    legend: {
      data: ['countIn', 'countOut'],
      formatter: (name: string) => (name === 'countIn' ? '进入' : '出去'),
      textStyle: { color: '#8892a0', fontSize: 12 },
      top: 0,
    },
    grid: {
      left: 50,
      right: 20,
      bottom: 30,
      top: 40,
    },
    xAxis: {
      type: 'category' as const,
      data: xData,
      axisLine: { lineStyle: { color: '#1e293b' } },
      axisTick: { show: false },
      axisLabel: { color: '#8892a0', fontSize: 12 },
    },
    yAxis: {
      type: 'value' as const,
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } },
      axisLabel: { color: '#8892a0', fontSize: 12 },
    },
    series: [
      {
        name: 'countIn',
        type: isArea ? 'line' : ('bar' as const),
        data: inData,
        smooth: isArea,
        symbol: 'none',
        lineStyle: isArea ? { color: '#00d9ff', width: 2 } : undefined,
        areaStyle: isArea
          ? {
              color: {
                type: 'linear' as const,
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  { offset: 0, color: 'rgba(0,217,255,0.3)' },
                  { offset: 1, color: 'rgba(0,217,255,0)' },
                ],
              },
            }
          : undefined,
        itemStyle: {
          color: '#00d9ff',
          borderRadius: isArea ? undefined : [4, 4, 0, 0],
        },
      },
      {
        name: 'countOut',
        type: isArea ? 'line' : ('bar' as const),
        data: outData,
        smooth: isArea,
        symbol: 'none',
        lineStyle: isArea ? { color: '#00ff88', width: 2 } : undefined,
        areaStyle: isArea
          ? {
              color: {
                type: 'linear' as const,
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  { offset: 0, color: 'rgba(0,255,136,0.3)' },
                  { offset: 1, color: 'rgba(0,255,136,0)' },
                ],
              },
            }
          : undefined,
        itemStyle: {
          color: '#00ff88',
          borderRadius: isArea ? undefined : [4, 4, 0, 0],
        },
      },
    ],
  }
})

// 加载设备列表
onMounted(() => {
  fetch('/api/devices')
    .then((res) => (res.ok ? res.json() : null))
    .then((json) => {
      const list = json?.data || []
      deviceOptions.value = Array.isArray(list)
        ? list.map((d: any) => ({ id: d.id, name: d.name }))
        : []
    })
    .catch(() => {})
  fetchData()
})

async function fetchData() {
  if (!startDate.value || !endDate.value) return
  loading.value = true
  try {
    const params = new URLSearchParams({
      startDate: startDate.value,
      endDate: endDate.value,
    })
    if (selectedDevice.value && selectedDevice.value !== '__all__') {
      params.set('deviceId', selectedDevice.value)
    }
    const res = await fetch(`/api/traffic/history?${params}`)
    if (res.ok) {
      const json = await res.json()
      const apiData = json.data || json
      data.value = apiData.daily || []
      deviceDailyData.value = apiData.dailyDeviceData || []
    }
  } catch {
    // Keep empty
  } finally {
    loading.value = false
  }
}

function handleExportCSV() {
  if (data.value.length === 0) return

  const BOM = '\uFEFF'
  const deviceLabel =
    selectedDevice.value === '__all__'
      ? '门店汇总'
      : `设备${selectedDevice.value}`
  const headers = `日期,${deviceLabel}进入人数,${deviceLabel}出去人数\n`
  const rows = data.value
    .map((d) => `${d.date},${d.countIn},${d.countOut}`)
    .join('\n')
  const csv = BOM + headers + rows

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `客流数据_${startDate.value}_${endDate.value}.csv`
  link.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
:deep(.history-date-picker .ant-picker) {
  background-color: #0a192f !important;
  border-color: #1e293b !important;
  color: #ffffff !important;
  height: 36px !important;
  border-radius: 0.375rem !important;
  width: 160px !important;
}

:deep(.history-date-picker .ant-picker-input > input) {
  color: #ffffff !important;
}

:deep(.history-date-picker .ant-picker-suffix) {
  color: #8892a0 !important;
}

:deep(.ant-picker-dropdown) {
  background-color: #112240 !important;
  border-color: #1e293b !important;
}

:deep(.ant-picker-panel) {
  background-color: #112240 !important;
  border-color: #1e293b !important;
}

:deep(.ant-picker-header) {
  border-bottom-color: #1e293b !important;
}

:deep(.ant-picker-header button) {
  color: #8892a0 !important;
}

:deep(.ant-picker-content th) {
  color: #8892a0 !important;
}

:deep(.ant-picker-cell) {
  color: #ffffff !important;
}

:deep(.ant-picker-cell-in-view .ant-picker-cell-inner) {
  color: #ffffff !important;
}

:deep(.ant-picker-cell:hover .ant-picker-cell-inner) {
  background-color: #172a45 !important;
}

:deep(.ant-picker-cell-selected .ant-picker-cell-inner) {
  background-color: #00d9ff !important;
  color: #0a192f !important;
}

:deep(.ant-picker-today .ant-picker-cell-inner::before) {
  border-color: #00d9ff !important;
}

:deep(.ant-picker-footer) {
  border-top-color: #1e293b !important;
}

:deep(.ant-select-selector) {
  background-color: #0a192f !important;
  border-color: #1e293b !important;
  color: #ffffff !important;
  height: 36px !important;
  border-radius: 0.375rem !important;
}

:deep(.ant-select-selection-item) {
  color: #ffffff !important;
  line-height: 34px !important;
}

:deep(.ant-select-arrow) {
  color: #8892a0 !important;
}

:deep(.ant-select-dropdown) {
  background-color: #0a192f !important;
  border-color: #1e293b !important;
}

:deep(.ant-select-item) {
  color: #ffffff !important;
}

:deep(.ant-select-item-option-active) {
  background-color: #172a45 !important;
}

:deep(.ant-select-item-option-selected) {
  background-color: #172a45 !important;
  font-weight: 600;
}
</style>
