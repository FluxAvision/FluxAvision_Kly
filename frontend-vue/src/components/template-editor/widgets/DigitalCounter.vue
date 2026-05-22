<script setup lang="ts">
/**
 * 数字计数器组件
 */
import { computed } from 'vue'
import type { ComponentConfig } from '@/types/template-editor'

const props = defineProps<{
  config: ComponentConfig
  data?: { value?: number }
}>()

const title = computed(() => props.config.props?.title || '来访总人数')
const digits = computed(() => props.config.props?.digits || 8)
const value = computed(() => {
  const v = props.data?.value ?? 0
  return String(v).padStart(digits.value, '0').split('')
})
</script>

<template>
  <div class="w-full h-full flex flex-col items-center justify-center gap-3">
    <!-- 标题 -->
    <div
      v-if="title"
      class="px-6 py-2 rounded-full"
      style="background: rgba(74, 158, 255, 0.1); border: 1px solid rgba(74, 158, 255, 0.3);"
    >
      <span class="text-base text-white font-medium" :style="config.styles?.fontSize ? { fontSize: config.styles.fontSize + 'px' } : undefined">{{ title }}</span>
    </div>

    <!-- 数字计数器 -->
    <div class="flex items-center gap-2">
      <div
        v-for="(digit, idx) in value"
        :key="idx"
        class="w-12 h-16 flex items-center justify-center rounded-lg text-3xl font-bold text-white" :style="config.styles?.fontSize ? { fontSize: config.styles.fontSize + 'px', width: (config.styles.fontSize * 1.2) + 'px', height: (config.styles.fontSize * 1.6) + 'px' } : undefined"
        style="background: rgba(10, 26, 58, 0.8); border: 1px solid rgba(74, 158, 255, 0.4); box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.3), 0 0 10px rgba(74, 158, 255, 0.1);"
      >
        {{ digit }}
      </div>
    </div>
  </div>
</template>
