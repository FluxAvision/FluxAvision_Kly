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

// 布局方式
const layout = computed(() => props.config.props?.layout || 'vertical')

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
  <!-- horizontal（左右排列） -->
  <div
    v-if="layout === 'horizontal'"
    class="w-full h-full rounded-xl overflow-hidden flex items-center px-6"
    :style="{
      background: config.styles?.backgroundColor || 'linear-gradient(135deg, rgba(30, 58, 95, 0.8), rgba(15, 40, 71, 0.8))',
      border: '1px solid rgba(74, 158, 255, 0.25)',
      justifyContent: config.props?.titleAlign === 'left' ? 'flex-start' : (config.props?.titleAlign === 'right' ? 'flex-end' : 'center'),
    }"
  >
    <span
      :style="{
        fontSize: (config.props?.titleFontSize || 16) + 'px',
        fontWeight: config.props?.titleBold ? 'bold' : 'normal',
        color: config.props?.titleColor || cardColor,
        whiteSpace: 'nowrap',
        marginRight: '12px',
      }"
    >{{ title }}</span>
    <span
      :style="{
        fontSize: (config.styles?.fontSize || 32) + 'px',
        fontWeight: 'bold',
        color: config.styles?.color || '#ffffff',
        textShadow: `0 0 20px ${cardColor}80`,
      }"
    >{{ value.toLocaleString() }}</span>
  </div>

  <!-- vertical（上下排列，默认） -->
  <div
    v-else
    class="w-full h-full rounded-xl overflow-hidden flex flex-col"
    :style="{
      background: config.styles?.backgroundColor || 'linear-gradient(135deg, rgba(30, 58, 95, 0.8), rgba(15, 40, 71, 0.8))',
      border: '1px solid rgba(74, 158, 255, 0.25)',
      justifyContent: config.props?.titleAlign === 'left' ? 'flex-start' : (config.props?.titleAlign === 'right' ? 'flex-end' : 'center'),
    }"
  >
    <!-- 标题（顶部留白24px，跟随卡片统一背景） -->
    <div
      :style="{
        display: 'flex',
        alignItems: 'center',
        padding: '24px 12px 0',
        fontSize: (config.props?.titleFontSize || 14) + 'px',
        fontWeight: config.props?.titleBold ? 'bold' : 'normal',
        justifyContent: config.props?.titleAlign || 'center',
      }"
    >
      <span :style="{ color: config.props?.titleColor || undefined }">{{ title }}</span>
    </div>

    <!-- 内容区域 -->
    <div class="flex-1 flex flex-col items-center justify-center" style="padding: 8px 16px;">
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
    </div>
  </div>
</template>
