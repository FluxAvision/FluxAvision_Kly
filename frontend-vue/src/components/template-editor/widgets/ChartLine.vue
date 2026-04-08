<script setup lang="ts">
/**
 * 折线图组件
 */
import { computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import type { ComponentConfig } from '@/types/template-editor'
import type { HourlyData } from '@/components/large-screen/composables/useLargeScreenData'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent])

const props = defineProps<{
  config: ComponentConfig
  data?: { hourlyData?: HourlyData[] }
}>()

const title = computed(() => props.config.props?.title || '客流趋势')
const showIn = computed(() => props.config.props?.showIn ?? true)
const showOut = computed(() => props.config.props?.showOut ?? true)
const smooth = computed(() => props.config.props?.smooth ?? true)
const areaStyle = computed(() => props.config.props?.areaStyle ?? true)

const hourlyData = computed(() => props.data?.hourlyData || [])

const chartOption = computed(() => {
  const series = []

  if (showIn.value) {
    series.push({
      type: 'line',
      name: '进入',
      smooth: smooth.value,
      symbol: 'none',
      areaStyle: areaStyle.value ? {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0.05, color: 'rgba(0, 217, 255, 0.3)' },
            { offset: 0.95, color: 'rgba(0, 217, 255, 0)' },
          ],
        },
      } : undefined,
      lineStyle: { color: '#00d9ff', width: 2 },
      itemStyle: { color: '#00d9ff' },
      data: hourlyData.value.map(h => h.countIn),
    })
  }

  if (showOut.value) {
    series.push({
      type: 'line',
      name: '出去',
      smooth: smooth.value,
      symbol: 'none',
      areaStyle: areaStyle.value ? {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0.05, color: 'rgba(0, 255, 136, 0.3)' },
            { offset: 0.95, color: 'rgba(0, 255, 136, 0)' },
          ],
        },
      } : undefined,
      lineStyle: { color: '#00ff88', width: 2 },
      itemStyle: { color: '#00ff88' },
      data: hourlyData.value.map(h => h.countOut),
    })
  }

  return {
    tooltip: {
      backgroundColor: 'rgba(23, 42, 69, 0.9)',
      borderColor: '#1e293b',
      borderRadius: 8,
      textStyle: { color: '#ffffff' },
    },
    grid: { left: 50, right: 20, top: 40, bottom: 30 },
    xAxis: {
      type: 'category',
      data: hourlyData.value.map(h => h.hour),
      axisLine: { lineStyle: { color: '#1e293b' } },
      axisLabel: { color: '#8892a0', fontSize: 11 },
      interval: 3,
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#1e293b' } },
      axisLabel: { color: '#8892a0', fontSize: 11 },
      splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } },
    },
    series,
  }
})
</script>

<template>
  <div class="w-full h-full rounded-lg overflow-hidden flex flex-col" style="background: rgba(10, 30, 60, 0.5); border: 1px solid rgba(74, 158, 255, 0.15);">
    <h3 class="text-sm text-[#8892a0] px-4 pt-3 flex-shrink-0">{{ title }}</h3>
    <div class="flex-1 min-h-0 px-2 pb-2">
      <VChart
        v-if="hourlyData.length > 0"
        :option="chartOption"
        autoresize
        style="width: 100%; height: 100%;"
      />
      <div v-else class="w-full h-full flex items-center justify-center text-[#8892a0] text-sm">
        暂无趋势数据
      </div>
    </div>
  </div>
</template>
