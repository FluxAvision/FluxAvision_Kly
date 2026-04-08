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
</script>

<template>
  <div class="w-full h-full">
    <!-- DataV 边框 -->
    <dv-border-box-1 v-if="borderType === 'dv-border-box-1'" class="w-full h-full">
      <slot />
    </dv-border-box-1>
    <dv-border-box-2 v-else-if="borderType === 'dv-border-box-2'" class="w-full h-full">
      <slot />
    </dv-border-box-2>
    <dv-border-box-3 v-else-if="borderType === 'dv-border-box-3'" class="w-full h-full">
      <slot />
    </dv-border-box-3>
    <dv-border-box-4 v-else-if="borderType === 'dv-border-box-4'" class="w-full h-full">
      <slot />
    </dv-border-box-4>
    <dv-border-box-5 v-else-if="borderType === 'dv-border-box-5'" class="w-full h-full">
      <slot />
    </dv-border-box-5>
    <dv-border-box-6 v-else-if="borderType === 'dv-border-box-6'" class="w-full h-full">
      <slot />
    </dv-border-box-6>
    <dv-border-box-7 v-else-if="borderType === 'dv-border-box-7'" class="w-full h-full">
      <slot />
    </dv-border-box-7>
    <dv-border-box-8 v-else-if="borderType === 'dv-border-box-8'" class="w-full h-full">
      <slot />
    </dv-border-box-8>
    <dv-border-box-9 v-else-if="borderType === 'dv-border-box-9'" class="w-full h-full">
      <slot />
    </dv-border-box-9>
    <dv-border-box-10 v-else-if="borderType === 'dv-border-box-10'" class="w-full h-full">
      <slot />
    </dv-border-box-10>
    <dv-border-box-11 v-else-if="borderType === 'dv-border-box-11'" class="w-full h-full">
      <slot />
    </dv-border-box-11>
    <dv-border-box-12 v-else-if="borderType === 'dv-border-box-12'" class="w-full h-full">
      <slot />
    </dv-border-box-12>
    <dv-border-box-13 v-else-if="borderType === 'dv-border-box-13'" class="w-full h-full">
      <slot />
    </dv-border-box-13>
    <!-- 默认 -->
    <div v-else class="w-full h-full border border-[#1e293b] rounded-lg">
      <slot />
    </div>
  </div>
</template>
