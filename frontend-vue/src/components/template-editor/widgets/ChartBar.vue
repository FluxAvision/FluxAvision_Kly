<script setup lang="ts">
/**
 * 柱状图组件
 */
import { computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import type { ComponentConfig } from '@/types/template-editor'
import type { HourlyData } from '@/components/large-screen/composables/useLargeScreenData'

use([CanvasRenderer, BarChart, GridComponent, TooltipComponent])

const props = defineProps<{
  config: ComponentConfig
  data?: { hourlyData?: HourlyData[] }
}>()

const title = computed(() => props.config.props?.title || '客流对比')
const showIn = computed(() => props.config.props?.showIn ?? true)
const showOut = computed(() => props.config.props?.showOut ?? true)

const hourlyData = computed(() => props.data?.hourlyData || [])

const chartOption = computed(() => {
  const series = []

  if (showIn.value) {
    series.push({
      type: 'bar',
      name: '进入',
      barWidth: '35%',
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
      data: hourlyData.value.map(h => h.countIn),
    })
  }

  if (showOut.value) {
    series.push({
      type: 'bar',
      name: '出去',
      barWidth: '35%',
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
      data: hourlyData.value.map(h => h.countOut),
    })
  }

  return {
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
        暂无数据
      </div>
    </div>
  </div>
</template>
