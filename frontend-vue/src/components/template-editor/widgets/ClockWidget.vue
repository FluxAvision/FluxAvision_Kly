<script setup lang="ts">
/**
 * 实时时间组件
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { ComponentConfig } from '@/types/template-editor'

const props = defineProps<{
  config: ComponentConfig
  data?: any
}>()

const currentTime = ref('')
let interval: ReturnType<typeof setInterval> | null = null

const showDate = computed(() => props.config.props?.showDate ?? true)
const showWeek = computed(() => props.config.props?.showWeek ?? true)
const showTime = computed(() => props.config.props?.showTime ?? true)
const format = computed(() => props.config.props?.format || 'full')

function updateTime() {
  const now = new Date()
  const weekDays = ['日', '一', '二', '三', '四', '五', '六']

  const year = now.getFullYear()
  const month = now.getMonth() + 1
  const day = now.getDate()
  const week = weekDays[now.getDay()]
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  const seconds = String(now.getSeconds()).padStart(2, '0')

  const parts: string[] = []

  if (showDate.value) {
    parts.push(`${year}年${month}月${day}日`)
  }

  if (showWeek.value) {
    parts.push(`星期${week}`)
  }

  if (showTime.value) {
    parts.push(`${hours}:${minutes}:${seconds}`)
  }

  currentTime.value = parts.join(' ')
}

onMounted(() => {
  updateTime()
  interval = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (interval) clearInterval(interval)
})
</script>

<template>
  <div class="w-full h-full flex items-center justify-center overflow-hidden">
    <span
      class="text-white font-mono whitespace-nowrap"
      :style="{
        fontSize: config.props?.fontSize ? `${config.props.fontSize}px` : undefined,
        color: config.styles?.color || '#ffffff',
        textShadow: '0 0 10px rgba(0, 217, 255, 0.3)',
      }"
    >
      {{ currentTime }}
    </span>
  </div>
</template>