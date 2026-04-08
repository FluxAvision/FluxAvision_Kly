<script setup lang="ts">
/**
 * DataV 装饰组件
 */
import { computed } from 'vue'
import type { ComponentConfig } from '@/types/template-editor'

const props = defineProps<{
  config: ComponentConfig
  data?: any
}>()

const decorationType = computed(() => props.config.props?.decorationType || 'dv-decoration-1')
</script>

<template>
  <div class="w-full h-full flex items-center justify-center">
    <dv-decoration-1 v-if="decorationType === 'dv-decoration-1'" class="w-full h-full" />
    <dv-decoration-2 v-else-if="decorationType === 'dv-decoration-2'" class="w-full h-full" />
    <dv-decoration-3 v-else-if="decorationType === 'dv-decoration-3'" class="w-full h-full" />
    <dv-decoration-4 v-else-if="decorationType === 'dv-decoration-4'" class="w-full h-full" />
    <dv-decoration-5 v-else-if="decorationType === 'dv-decoration-5'" class="w-full h-full" />
    <dv-decoration-6 v-else-if="decorationType === 'dv-decoration-6'" class="w-full h-full" />
    <dv-decoration-7 v-else-if="decorationType === 'dv-decoration-7'" class="w-full h-full">
      {{ config.props?.text || 'Decoration' }}
    </dv-decoration-7>
    <dv-decoration-8 v-else-if="decorationType === 'dv-decoration-8'" class="w-full h-full" />
    <dv-decoration-9 v-else-if="decorationType === 'dv-decoration-9'" class="w-full h-full" />
    <dv-decoration-10 v-else-if="decorationType === 'dv-decoration-10'" class="w-full h-full" />
    <dv-decoration-11 v-else-if="decorationType === 'dv-decoration-11'" class="w-full h-full">
      {{ config.props?.text || 'Decoration' }}
    </dv-decoration-11>
    <dv-decoration-12 v-else-if="decorationType === 'dv-decoration-12'" class="w-full h-full" />
    <!-- 默认装饰 -->
    <div v-else class="w-full h-full border-t border-[#00d9ff]/30" />
  </div>
</template>
