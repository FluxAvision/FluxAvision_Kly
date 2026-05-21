<template>
  <div class="space-y-4">
    <!-- Toolbar -->
    <div class="bg-[#112240] border border-[#1e293b] rounded-lg p-4">
      <div class="flex items-center gap-4 flex-wrap">
        <!-- 维度切换 -->
        <div class="flex border border-[#1e293b] rounded-lg overflow-hidden">
          <button
            v-for="dim in dimensionOptions"
            :key="dim.value"
            @click="switchDimension(dim.value)"
            :class="[
              'px-3 py-2 text-xs font-medium transition-colors cursor-pointer',
              dimension === dim.value
                ? 'bg-[#00d9ff] text-[#0a192f]'
                : 'bg-[#0a192f] text-[#8892a0] hover:text-white',
            ]"
          >
            {{ dim.label }}
          </button>
        </div>

        <!-- 日期选择 -->
        <template v-if="dimension === 'hour'">
          <div class="flex items-center gap-2">
            <label class="text-sm text-[#8892a0]">选择日期</label>
            <a-date-picker
              :value="startDate ? dayjs(startDate) : null"
              @change="(_d: any, dateStr: string) => { startDate = dateStr; endDate = dateStr }"
              class="history-date-picker"
              placeholder=""
            />
          </div>
        </template>
        <template v-else>
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
        </template>

        <!-- 设备筛选 -->
        <div class="flex items-center gap-2">
          <label class="text-sm text-[#8892a0]">设备筛选</label>
          <a-select
            :value="selectedDevice"
            @change="selectedDevice = $event"
            class="w-44"
            popup-class-name="device-select-dropdown"
          >
            <a-select-option value="__all__">门店汇总(全部设备)</a-select-option>
            <a-select-option
              v-for="d in deviceOptions"
              :key="d.id"
              :value="d.id"
            >
              {{ d.name }}
            </a-select-option>
          </a-select>
        </div>

        <!-- 查询按钮 -->
        <button
          @click="fetchData"
          :disabled="loading"
          class="bg-[#00d9ff] text-[#0a192f] rounded-md px-4 py-2 text-xs font-medium transition-colors flex items-center gap-2 hover:bg-[#00d9ff]/80 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
          查询
        </button>

      </div>

      <!-- 视图说明 -->
      <div class="mt-2">
        <span class="text-xs text-[#8892a0]">
          {{ dimensionLabel }}
          ·
          {{ isStoreView ? '门店汇总(所有设备客流之和)' : `单设备(${selectedDeviceName})` }}
        </span>
      </div>
    </div>

    <!-- 数值汇总 -->
    <div v-if="!loading && data.length > 0" class="grid grid-cols-3 gap-4">
      <div class="bg-[#112240] border border-[#1e293b] rounded-lg p-4 text-center">
        <p class="text-xs text-[#8892a0] mb-1">总进入</p>
        <p class="text-xl font-bold text-[#00d9ff]">{{ totalIn.toLocaleString() }}</p>
      </div>
      <div class="bg-[#112240] border border-[#1e293b] rounded-lg p-4 text-center">
        <p class="text-xs text-[#8892a0] mb-1">总出去</p>
        <p class="text-xl font-bold text-[#00ff88]">{{ totalOut.toLocaleString() }}</p>
      </div>
      <div class="bg-[#112240] border border-[#1e293b] rounded-lg p-4 text-center">
        <p class="text-xs text-[#8892a0] mb-1">{{ avgLabel }}</p>
        <p class="text-xl font-bold text-[#4a9eff]">{{ averageValue.toLocaleString() }}</p>
      </div>
    </div>

    <!-- Chart -->
    <div class="bg-[#112240] border border-[#1e293b] rounded-lg p-5">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-white font-medium">
          {{ dimensionTitle }}
          {{ isStoreView ? '(门店汇总)' : '(单设备)' }}
        </h3>
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
            <LineChart class="w-3.5 h-3.5" /> 趋势图
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
            <BarChart3 class="w-3.5 h-3.5" /> 柱状图
          </button>
        </div>
      </div>
      <div v-if="loading" class="h-[350px] w-full bg-[#1e293b] rounded-md animate-pulse" />
      <div v-else-if="data.length === 0" class="flex items-center justify-center h-[350px] text-[#8892a0]">
        暂无数据
      </div>
      <v-chart v-else :option="chartOption" autoresize class="w-full" style="height: 350px" />
    </div>

    <!-- 数据明细表格 -->
    <div v-if="!loading && data.length > 0" class="bg-[#112240] border border-[#1e293b] rounded-lg p-5">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-white font-medium">数据明细</h3>
        <div class="flex items-center gap-3">
          <span class="text-xs text-[#8892a0]">{{ data.length }} 条记录</span>
          <button
            @click="handleExportCSV"
            class="border border-[#1e293b] text-[#8892a0] hover:text-white hover:bg-[#172a45] rounded-md px-3 py-1.5 text-xs font-medium transition-colors flex items-center gap-1.5"
          >
            <Download class="w-3.5 h-3.5" /> 导出CSV
          </button>
        </div>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-[#1e293b]">
              <th class="text-left py-2 px-3 text-[#8892a0] font-medium">{{ dimension === 'hour' ? '时段' : '日期' }}</th>
              <th class="text-right py-2 px-3 text-[#00d9ff] font-medium">进入</th>
              <th class="text-right py-2 px-3 text-[#00ff88] font-medium">出去</th>
              <th class="text-right py-2 px-3 text-[#4a9eff] font-medium">净流入</th>
              <th v-if="dimension === 'hour'" class="text-center py-2 px-3 text-[#8892a0] font-medium" style="width: 100px">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, idx) in paginatedData"
              :key="(currentPage - 1) * PAGE_SIZE + idx"
              class="border-b border-[#1e293b]/50 hover:bg-[#172a45] transition-colors"
            >
              <td class="py-2 px-3 text-white">{{ row.label }}</td>
              <td class="py-2 px-3 text-right text-white">
                <template v-if="editingRowIndex === (currentPage - 1) * PAGE_SIZE + idx">
                  <input
                    v-model.number="editCountIn"
                    type="number"
                    min="0"
                    class="w-20 bg-[#0a192f] border border-[#1e293b] rounded px-2 py-1 text-white text-right text-sm"
                  />
                </template>
                <template v-else>
                  {{ row.countIn.toLocaleString() }}
                </template>
              </td>
              <td class="py-2 px-3 text-right text-white">
                <template v-if="editingRowIndex === (currentPage - 1) * PAGE_SIZE + idx">
                  <input
                    v-model.number="editCountOut"
                    type="number"
                    min="0"
                    class="w-20 bg-[#0a192f] border border-[#1e293b] rounded px-2 py-1 text-white text-right text-sm"
                  />
                </template>
                <template v-else>
                  {{ row.countOut.toLocaleString() }}
                </template>
              </td>
              <td class="py-2 px-3 text-right" :class="(row.countIn - row.countOut) >= 0 ? 'text-[#00d9ff]' : 'text-[#f59e0b]'">
                {{ Math.max(0, row.countIn - row.countOut).toLocaleString() }}
              </td>
              <td v-if="dimension === 'hour'" class="py-2 px-3 text-center">
                <template v-if="editingRowIndex === (currentPage - 1) * PAGE_SIZE + idx">
                  <button
                    @click="saveEdit(row.label)"
                    :disabled="correcting"
                    class="text-xs text-[#00d9ff] hover:text-[#00d9ff]/80 mr-2 disabled:opacity-50 cursor-pointer"
                  >
                    保存
                  </button>
                  <button
                    @click="cancelEdit"
                    :disabled="correcting"
                    class="text-xs text-[#8892a0] hover:text-white disabled:opacity-50 cursor-pointer"
                  >
                    取消
                  </button>
                </template>
                <button
                  v-else
                  @click="startEdit((currentPage - 1) * PAGE_SIZE + idx, row)"
                  class="text-[#8892a0] hover:text-[#00d9ff] transition-colors cursor-pointer"
                >
                  <Pencil class="w-3.5 h-3.5 inline" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分页 -->
      <div v-if="totalPages > 1" class="flex items-center justify-between mt-4 pt-4 border-t border-[#1e293b]">
        <span class="text-xs text-[#8892a0]">共 {{ data.length }} 条，第 {{ currentPage }}/{{ totalPages }} 页</span>
        <div class="flex items-center gap-2">
          <button
            @click="goToPage(currentPage - 1)"
            :disabled="currentPage === 1"
            class="px-3 py-1.5 text-xs rounded border border-[#1e293b] text-[#8892a0] hover:text-white hover:bg-[#172a45] transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            上一页
          </button>
          <button
            v-for="p in paginationPages"
            :key="p"
            @click="goToPage(p)"
            :class="[
              'px-3 py-1.5 text-xs rounded transition-colors cursor-pointer',
              p === currentPage
                ? 'bg-[#00d9ff] text-[#0a192f]'
                : 'border border-[#1e293b] text-[#8892a0] hover:text-white hover:bg-[#172a45]',
            ]"
          >
            {{ p }}
          </button>
          <button
            @click="goToPage(currentPage + 1)"
            :disabled="currentPage === totalPages"
            class="px-3 py-1.5 text-xs rounded border border-[#1e293b] text-[#8892a0] hover:text-white hover:bg-[#172a45] transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            下一页
          </button>
        </div>
      </div>

    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Download, BarChart3, LineChart, Pencil } from 'lucide-vue-next'
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

interface HistoryRow {
  label: string
  countIn: number
  countOut: number
}

interface DeviceOption {
  id: string
  name: string
}

const DEVICE_COLORS = ['#00d9ff', '#00ff88', '#ff9500', '#a855f7', '#f43f5e', '#06b6d4', '#f97316', '#10b981']

const dimensionOptions = [
  { value: 'hour', label: '小时' },
  { value: 'day', label: '天' },
  { value: 'week', label: '周' },
  { value: 'month', label: '月' },
  { value: 'year', label: '年' },
]

const today = new Date()
const todayStr = today.toISOString().split('T')[0]

const dimension = ref<string>('hour')
const startDate = ref(todayStr)
const endDate = ref(todayStr)
const selectedDevice = ref('__all__')
const deviceOptions = ref<DeviceOption[]>([])
const data = ref<HistoryRow[]>([])
const loading = ref(false)
const chartType = ref<'area' | 'bar'>('area')

// 分页
const PAGE_SIZE = 20
const currentPage = ref(1)
const totalPages = computed(() => Math.max(1, Math.ceil(data.value.length / PAGE_SIZE)))
const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return data.value.slice(start, start + PAGE_SIZE)
})
const paginationPages = computed(() => {
  const total = totalPages.value
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }
  const current = currentPage.value
  const pages: number[] = [1]
  const start = Math.max(2, current - 1)
  const end = Math.min(total - 1, current + 1)
  if (start > 2) pages.push(-1) // ellipsis marker
  for (let i = start; i <= end; i++) pages.push(i)
  if (end < total - 1) pages.push(-2) // ellipsis marker
  pages.push(total)
  return pages
})
function goToPage(p: number) {
  if (p < 1 || p > totalPages.value) return
  currentPage.value = p
  // 翻页时取消编辑状态
  editingRowIndex.value = null
}

// 修正功能状态
const editingRowIndex = ref<number | null>(null)
const editCountIn = ref(0)
const editCountOut = ref(0)
const correcting = ref(false)

const isStoreView = computed(() => selectedDevice.value === '__all__')

const selectedDeviceName = computed(() => {
  if (selectedDevice.value === '__all__') return '全部'
  return deviceOptions.value.find(d => d.id === selectedDevice.value)?.name || ''
})

const dimensionLabel = computed(() => {
  const dim = dimensionOptions.find(d => d.value === dimension.value)
  return dim ? `当前维度: ${dim.label}` : ''
})

const dimensionTitle = computed(() => {
  const dim = dimensionOptions.find(d => d.value === dimension.value)
  return dim ? `${dim.label}度客流数据` : '历史客流数据'
})

const avgLabel = computed(() => {
  const dim = dimensionOptions.find(d => d.value === dimension.value)
  return dim ? `平均${dim.label}` : '平均值'
})

const totalIn = computed(() => data.value.reduce((s, d) => s + d.countIn, 0))
const totalOut = computed(() => data.value.reduce((s, d) => s + d.countOut, 0))
const averageValue = computed(() => {
  if (data.value.length === 0) return 0
  return Math.round(totalIn.value / data.value.length)
})

const chartOption = computed(() => {
  const xData = data.value.map(d => d.label)
  const inData = data.value.map(d => d.countIn)
  const outData = data.value.map(d => d.countOut)
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
      axisLabel: {
        color: '#8892a0',
        fontSize: 11,
        rotate: dimension.value === 'hour' ? 0 : 35,
      },
    },
    yAxis: {
      type: 'value' as const,
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } },
      axisLabel: { color: '#8892a0', fontSize: 12 },
      min: 0,
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
                x: 0, y: 0, x2: 0, y2: 1,
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
                x: 0, y: 0, x2: 0, y2: 1,
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

function switchDimension(dim: string) {
  dimension.value = dim
  const today = new Date()
  const todayStr = today.toISOString().split('T')[0]
  if (dim === 'hour') {
    startDate.value = todayStr
    endDate.value = todayStr
  } else if (dim === 'day' || dim === 'week') {
    const d = new Date(today)
    d.setDate(d.getDate() - 29)
    startDate.value = d.toISOString().split('T')[0]
    endDate.value = todayStr
  } else if (dim === 'month') {
    const d = new Date(today.getFullYear(), 0, 1)
    startDate.value = d.toISOString().split('T')[0]
    endDate.value = todayStr
  } else if (dim === 'year') {
    const d = new Date(today)
    d.setFullYear(d.getFullYear() - 2)
    startDate.value = d.toISOString().split('T')[0]
    endDate.value = todayStr
  }
  fetchData()
}

// 加载设备列表
onMounted(() => {
  fetch('/api/devices')
    .then(res => res.ok ? res.json() : null)
    .then(json => {
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
      dimension: dimension.value,
    })
    if (selectedDevice.value && selectedDevice.value !== '__all__') {
      params.set('deviceId', selectedDevice.value)
    }
    const res = await fetch(`/api/traffic/history?${params}`)
    if (res.ok) {
      const json = await res.json()
      const apiData = json.data || json
      data.value = apiData.data || []
      // 重置分页
      currentPage.value = 1
    }
  } catch {
    // Keep empty
  } finally {
    loading.value = false
  }
}

// 修正功能：开始编辑
function startEdit(idx: number, row: HistoryRow) {
  editingRowIndex.value = idx
  editCountIn.value = row.countIn
  editCountOut.value = row.countOut
}

function cancelEdit() {
  editingRowIndex.value = null
}

async function saveEdit(label: string) {
  // 从 label 提取 hour（格式 "HH:00"）
  const hour = parseInt(label.split(':')[0], 10)
  if (isNaN(hour)) return
  
  correcting.value = true
  try {
    const res = await fetch('/api/traffic/history/correct', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        date: startDate.value,
        hour: hour,
        countIn: editCountIn.value,
        countOut: editCountOut.value,
        deviceId: selectedDevice.value === '__all__' ? null : selectedDevice.value,
      }),
    })
    if (res.ok) {
      editingRowIndex.value = null
      await fetchData()  // 刷新数据
    }
  } catch {
    // 静默失败
  } finally {
    correcting.value = false
  }
}

function handleExportCSV() {
  if (data.value.length === 0) return

  const BOM = '\uFEFF'
  const deviceLabel = isStoreView ? '门店汇总' : `设备${selectedDevice.value}`
  const dimLabel = dimensionOptions.find(d => d.value === dimension.value)?.label || ''
  const headers = `${dimLabel},${deviceLabel}进入人数,${deviceLabel}出去人数\n`
  const rows = data.value
    .map(d => `${d.label},${d.countIn},${d.countOut}`)
    .join('\n')
  const csv = BOM + headers + rows

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `客流数据_${dimension.value}_${startDate.value}_${endDate.value}.csv`
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
