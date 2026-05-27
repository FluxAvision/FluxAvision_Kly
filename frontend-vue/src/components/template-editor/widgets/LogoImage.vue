<script setup lang="ts">
import { computed } from 'vue'
import type { ComponentConfig } from '@/types/template-editor'
const props = defineProps<{ config: ComponentConfig; data?: any }>()
const logoSrc = computed(() => props.config.props?.logoSrc || '')
</script>
<template>
  <div class="w-full h-full flex items-center justify-center overflow-hidden bg-transparent">
    <img v-if="logoSrc" :src="logoSrc" class="w-full h-full" style="object-fit: contain;" alt="logo" />
    <div v-else class="flex flex-col items-center justify-center gap-2 text-[#5a6a80]">
      <svg class="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <rect x="3" y="3" width="18" height="18" rx="2" /><circle cx="8.5" cy="8.5" r="1.5" /><polyline points="21 15 16 10 5 21" />
      </svg>
      <span class="text-xs">上传 Logo</span>
    </div>
  </div>
</template>
