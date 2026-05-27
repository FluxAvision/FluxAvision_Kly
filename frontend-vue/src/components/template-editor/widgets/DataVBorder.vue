<script setup lang="ts">
/**
 * DataV 边框组件
 */
import { computed } from 'vue'
import type { ComponentConfig } from '@/types/template-editor'

const props = defineProps<{
  config: ComponentConfig
  data?: any
}>()

const borderType = computed(() => props.config.props?.borderType || 'dv-border-box-1')

// 装饰线颜色（DataV 支持 color: string[]）
const borderColors = computed(() => {
  const colors = props.config.props?.borderColors
  return Array.isArray(colors) && colors.length > 0 ? colors : undefined
})

// 边框背景色
const backgroundColor = computed(() => {
  return props.config.styles?.backgroundColor || undefined
})

// 确保子内容不溢出
const containerStyle = computed(() => ({
  width: '100%',
  height: '100%',
  overflow: 'hidden',
}))

// DataV BorderBox 尺寸继承
const borderStyle = computed(() => ({
  width: '100%',
  height: '100%',
}))
</script>

<template>
  <div :style="containerStyle">
    <!-- DataV 边框 -->
    <dv-border-box-1 v-if="borderType === 'dv-border-box-1'" :style="borderStyle" :color="borderColors" :backgroundColor="backgroundColor">
      <slot />
    </dv-border-box-1>
    <dv-border-box-2 v-else-if="borderType === 'dv-border-box-2'" :style="borderStyle" :color="borderColors" :backgroundColor="backgroundColor">
      <slot />
    </dv-border-box-2>
    <dv-border-box-3 v-else-if="borderType === 'dv-border-box-3'" :style="borderStyle" :color="borderColors" :backgroundColor="backgroundColor">
      <slot />
    </dv-border-box-3>
    <dv-border-box-4 v-else-if="borderType === 'dv-border-box-4'" :style="borderStyle" :color="borderColors" :backgroundColor="backgroundColor">
      <slot />
    </dv-border-box-4>
    <dv-border-box-5 v-else-if="borderType === 'dv-border-box-5'" :style="borderStyle" :color="borderColors" :backgroundColor="backgroundColor">
      <slot />
    </dv-border-box-5>
    <dv-border-box-6 v-else-if="borderType === 'dv-border-box-6'" :style="borderStyle" :color="borderColors" :backgroundColor="backgroundColor">
      <slot />
    </dv-border-box-6>
    <dv-border-box-7 v-else-if="borderType === 'dv-border-box-7'" :style="borderStyle" :color="borderColors" :backgroundColor="backgroundColor">
      <slot />
    </dv-border-box-7>
    <dv-border-box-8 v-else-if="borderType === 'dv-border-box-8'" :style="borderStyle" :color="borderColors" :backgroundColor="backgroundColor">
      <slot />
    </dv-border-box-8>
    <dv-border-box-9 v-else-if="borderType === 'dv-border-box-9'" :style="borderStyle" :color="borderColors" :backgroundColor="backgroundColor">
      <slot />
    </dv-border-box-9>
    <dv-border-box-10 v-else-if="borderType === 'dv-border-box-10'" :style="borderStyle" :color="borderColors" :backgroundColor="backgroundColor">
      <slot />
    </dv-border-box-10>
    <dv-border-box-11 v-else-if="borderType === 'dv-border-box-11'" :style="borderStyle" :color="borderColors" :backgroundColor="backgroundColor">
      <slot />
    </dv-border-box-11>
    <dv-border-box-12 v-else-if="borderType === 'dv-border-box-12'" :style="borderStyle" :color="borderColors" :backgroundColor="backgroundColor">
      <slot />
    </dv-border-box-12>
    <dv-border-box-13 v-else-if="borderType === 'dv-border-box-13'" :style="borderStyle" :color="borderColors" :backgroundColor="backgroundColor">
      <slot />
    </dv-border-box-13>
    <!-- 默认 -->
    <div v-else class="w-full h-full border border-[#1e293b] rounded-lg" :style="{ backgroundColor: backgroundColor || undefined }">
      <slot />
    </div>
  </div>
</template>
