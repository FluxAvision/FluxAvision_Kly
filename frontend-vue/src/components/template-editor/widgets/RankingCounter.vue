<script setup lang="ts">
import { computed } from 'vue'
import type { ComponentConfig } from '@/types/template-editor'

const props = defineProps<{ config: ComponentConfig; data?: { value?: number } }>()
const leftText = computed(() => props.config.props?.leftText || '您是第')
const rightText = computed(() => props.config.props?.rightText || '位到访的客户')
const value = computed(() => props.data?.value ?? 0)
const fontSize = computed(() => props.config.props?.counterFontSize || 20)
const textColor = computed(() => props.config.props?.textColor || '#ffffff')
const counterColor = computed(() => props.config.props?.counterColor || '#00d9ff')
const digits = computed(() => props.config.props?.digits || 6)
</script>

<template>
  <div class="w-full h-full flex items-center justify-center gap-2 overflow-hidden px-4">
    <span :style="{ fontSize: fontSize + 'px', color: textColor, whiteSpace: 'nowrap', flexShrink: 0 }">{{ leftText }}</span>
    <div class="flex items-center gap-1" :style="{ flexShrink: 0 }">
      <span v-for="i in digits" :key="i"
        class="inline-flex items-center justify-center rounded font-bold"
        :style="{
          fontSize: (fontSize * 1.5) + 'px',
          color: counterColor,
          textShadow: `0 0 10px ${counterColor}40`,
          minWidth: (fontSize * 1.2) + 'px',
          height: (fontSize * 2) + 'px',
        }"
      >
        {{ String(value).padStart(digits, '0')[i - 1] || '0' }}
      </span>
    </div>
    <span :style="{ fontSize: fontSize + 'px', color: textColor, whiteSpace: 'nowrap', flexShrink: 0 }">{{ rightText }}</span>
  </div>
</template>
