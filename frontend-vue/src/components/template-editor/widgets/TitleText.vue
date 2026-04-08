<script setup lang="ts">
/**
 * 标题/文本组件
 */
import { computed } from 'vue'
import type { ComponentConfig } from '@/types/template-editor'

const props = defineProps<{
  config: ComponentConfig
  data?: any
}>()

const isTitle = computed(() => props.config.type === 'title')
const text = computed(() => props.config.props?.text || props.config.name)
const level = computed(() => props.config.props?.level || 1)
const fontSize = computed(() => {
  if (isTitle.value) {
    switch (level.value) {
      case 1: return '2rem'
      case 2: return '1.5rem'
      case 3: return '1.25rem'
      default: return '1.5rem'
    }
  }
  return `${props.config.props?.fontSize || 14}px`
})
const fontWeight = computed(() => isTitle.value ? 'bold' : 'normal')
const textAlign = computed(() => props.config.props?.textAlign || 'center')
const color = computed(() => props.config.styles?.color || '#ffffff')
</script>

<template>
  <div class="w-full h-full flex items-center justify-center overflow-hidden">
    <h1
      v-if="isTitle && level === 1"
      class="truncate"
      :style="{ fontSize, fontWeight, textAlign, color, textShadow: '0 0 10px rgba(0, 217, 255, 0.4)' }"
    >
      {{ text }}
    </h1>
    <h2
      v-else-if="isTitle && level === 2"
      class="truncate"
      :style="{ fontSize, fontWeight, textAlign, color }"
    >
      {{ text }}
    </h2>
    <h3
      v-else-if="isTitle && level === 3"
      class="truncate"
      :style="{ fontSize, fontWeight, textAlign, color }"
    >
      {{ text }}
    </h3>
    <p
      v-else
      class="truncate"
      :style="{ fontSize, fontWeight, textAlign, color }"
    >
      {{ text }}
    </p>
  </div>
</template>
