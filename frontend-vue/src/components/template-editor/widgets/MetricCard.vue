<script setup lang="ts">
/**
 * 指标卡片组件
 */
import { computed } from 'vue'
import type { ComponentConfig } from '@/types/template-editor'

const props = defineProps<{
  config: ComponentConfig
  data?: { value?: number; label?: string }
}>()

const title = computed(() => props.config.props?.title || props.data?.label || '指标')
const value = computed(() => props.data?.value ?? 0)
const showIcon = computed(() => props.config.props?.showIcon ?? true)

// 根据指标 key 确定颜色
const cardColor = computed(() => {
  const key = props.config.dataSource?.key
  const colors: Record<string, string> = {
    todayIn: '#00d9ff',
    todayOut: '#00ff88',
    currentIn: '#4a9eff',
    weekIn: '#ff9500',
    weekOut: '#a855f7',
    monthIn: '#f43f5e',
    monthOut: '#f97316',
    totalIn: '#06b6d4',
    totalOut: '#10b981',
  }
  return colors[key || ''] || '#00d9ff'
})
</script>

<template>
  <div
    class="w-full h-full rounded-xl overflow-hidden flex flex-col"
    style="background: linear-gradient(135deg, rgba(30, 58, 95, 0.8), rgba(15, 40, 71, 0.8)); border: 1px solid rgba(74, 158, 255, 0.25);"
  >
    <!-- 顶部装饰条 -->
    <div
      class="h-7 flex items-center justify-center"
      :style="{ background: `linear-gradient(90deg, ${cardColor}40, ${cardColor}15, ${cardColor}40)` }"
    >
      <span class="text-sm text-white/80 font-medium" :style="config.styles?.fontSize ? { fontSize: config.styles.fontSize + 'px' } : undefined">{{ title }}</span>
    </div>

    <!-- 内容区域 -->
    <div class="flex-1 flex flex-col items-center justify-center py-4">
      <!-- 图标 -->
      <svg v-if="showIcon" class="w-10 h-10 mb-2 text-white/70" viewBox="0 0 24 24" fill="currentColor">
        <circle cx="12" cy="5" r="3" />
        <path d="M6 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" fill="none" stroke="currentColor" stroke-width="1.5" />
      </svg>

      <!-- 数值 -->
      <p
        class="text-4xl font-bold text-white"
        :style="[
          { textShadow: `0 0 20px ${cardColor}80` },
          config.styles?.fontSize ? { fontSize: config.styles.fontSize + 'px' } : {},
        ]"
      >
        {{ value.toLocaleString() }}
      </p>
      <p class="text-sm text-white/50 mt-1" :style="config.styles?.fontSize ? { fontSize: Math.round(config.styles.fontSize * 0.5) + 'px' } : undefined">人</p>
    </div>
  </div>
</template>
