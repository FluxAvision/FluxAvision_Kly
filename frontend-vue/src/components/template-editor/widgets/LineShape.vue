<script setup lang="ts">
import { computed } from 'vue'
import type { ComponentConfig } from '@/types/template-editor'

const props = defineProps<{
  config: ComponentConfig
  data?: any
}>()

const direction = computed(() => props.config.props?.direction || 'horizontal')
const thickness = computed(() => props.config.props?.thickness || 2)
const lineColor = computed(() => props.config.props?.lineColor || '#00d9ff')
const lineOpacity = computed(() => props.config.props?.lineOpacity ?? 1)
</script>

<template>
  <div class="w-full h-full flex items-center justify-center overflow-hidden">
    <!-- 横向线条 -->
    <div v-if="direction === 'horizontal'" 
      class="rounded-full" 
      :style="{
        width: '100%',
        height: thickness + 'px',
        backgroundColor: lineColor,
        opacity: lineOpacity,
      }"
    />
    <!-- 竖向线条 -->
    <div v-else 
      class="rounded-full" 
      :style="{
        width: thickness + 'px',
        height: '100%',
        backgroundColor: lineColor,
        opacity: lineOpacity,
      }"
    />
  </div>
</template>
