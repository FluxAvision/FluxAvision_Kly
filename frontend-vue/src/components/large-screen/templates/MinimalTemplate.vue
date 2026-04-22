<script setup lang="ts">
import { computed } from 'vue'
import { X } from 'lucide-vue-next'
import type { LargeScreenConfig } from '../composables/useLargeScreenData'

const props = defineProps<{
  config: LargeScreenConfig
  metrics: Record<string, number>
  hourlyData: { hour: string; countIn: number; countOut: number }[]
  devices: { id: string; name: string; ip: string; status: string }[]
  storeLogo: string
  loading: boolean
  clockTime: string
  getLabel: (key: string) => string
}>()

const emit = defineEmits<{ close: [] }>()

const fallbackTitle = '\u6b22\u8fce\u60a8'

const displayMetrics = computed(() => {
  const configured = props.config.metrics?.slice(0, 4) || []
  const fallback = ['todayIn', 'monthIn', 'totalIn', 'totalOut']
  const keys = [...configured]

  fallback.forEach((key) => {
    if (keys.length < 4 && !keys.includes(key)) keys.push(key)
  })

  return keys.slice(0, 4).map((key) => ({
    key,
    label: props.getLabel(key),
    value: props.metrics[key] || 0,
  }))
})

const leftMetrics = computed(() => displayMetrics.value.slice(0, 2))
const rightMetrics = computed(() => displayMetrics.value.slice(2, 4))

const timeText = computed(() => {
  props.clockTime
  const now = new Date()
  const weekDays = [
    '\u661f\u671f\u65e5',
    '\u661f\u671f\u4e00',
    '\u661f\u671f\u4e8c',
    '\u661f\u671f\u4e09',
    '\u661f\u671f\u56db',
    '\u661f\u671f\u4e94',
    '\u661f\u671f\u516d',
  ]
  const date = `${now.getFullYear()}\u5e74${String(now.getMonth() + 1).padStart(2, '0')}\u6708${String(now.getDate()).padStart(2, '0')}\u65e5`
  const time = now.toLocaleTimeString('zh-CN', { hour12: false })
  return `${date}${weekDays[now.getDay()]} ${time}`
})
</script>

<template>
  <div class="minimal-template relative z-10 h-full w-full overflow-hidden">
    <div class="minimal-template__veil absolute inset-0" />

    <div class="relative z-10 flex h-full flex-col px-10 py-8">
      <div class="flex justify-end">
        <button
          class="minimal-template__close"
          @click="emit('close')"
        >
          <X class="h-5 w-5" />
        </button>
      </div>

      <div class="flex flex-1 flex-col items-center justify-center">
        <div class="minimal-template__title">
          {{ config.title || fallbackTitle }}
        </div>

        <div class="minimal-template__time">
          {{ timeText }}
        </div>

        <div class="minimal-template__metrics">
          <div class="minimal-template__column">
            <div
              v-for="item in leftMetrics"
              :key="item.key"
              class="minimal-template__metric"
            >
              <span class="minimal-template__metric-label">{{ item.label }}:</span>
              <span class="minimal-template__metric-value">{{ loading ? '--' : item.value.toLocaleString() }}</span>
            </div>
          </div>

          <div class="minimal-template__column">
            <div
              v-for="item in rightMetrics"
              :key="item.key"
              class="minimal-template__metric"
            >
              <span class="minimal-template__metric-label">{{ item.label }}:</span>
              <span class="minimal-template__metric-value">{{ loading ? '--' : item.value.toLocaleString() }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.minimal-template {
  color: #9f2338;
}

.minimal-template__veil {
  background:
    linear-gradient(180deg, rgba(232, 245, 255, 0.14) 0%, rgba(255, 255, 255, 0.08) 38%, rgba(146, 18, 31, 0.16) 100%),
    linear-gradient(0deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.12));
}

.minimal-template__close {
  display: flex;
  height: 42px;
  width: 42px;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  border: 1px solid rgba(159, 35, 56, 0.24);
  background: rgba(255, 255, 255, 0.42);
  color: #9f2338;
  transition: transform 0.2s ease, background-color 0.2s ease;
}

.minimal-template__close:hover {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.62);
}

.minimal-template__title {
  text-align: center;
  font-size: clamp(3rem, 4.6vw, 5.4rem);
  font-weight: 500;
  line-height: 1.15;
  letter-spacing: 0.08em;
  color: #a32338;
  text-shadow: 0 2px 8px rgba(255, 255, 255, 0.22);
}

.minimal-template__time {
  margin-top: 2rem;
  text-align: center;
  font-size: clamp(1.7rem, 2.2vw, 2.8rem);
  font-weight: 600;
  letter-spacing: 0.02em;
  color: #a32338;
}

.minimal-template__metrics {
  margin-top: 4.8rem;
  display: grid;
  width: min(100%, 1280px);
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: clamp(4rem, 16vw, 16rem);
  row-gap: 2rem;
}

.minimal-template__column {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.minimal-template__metric {
  display: flex;
  align-items: baseline;
  gap: 0.35rem;
  font-size: clamp(2.2rem, 3vw, 4rem);
  line-height: 1.2;
  color: #a32338;
  text-shadow: 0 1px 6px rgba(255, 255, 255, 0.18);
}

.minimal-template__metric-label {
  font-weight: 500;
}

.minimal-template__metric-value {
  font-weight: 700;
}

@media (max-width: 900px) {
  .minimal-template__metrics {
    margin-top: 3rem;
    grid-template-columns: 1fr;
    row-gap: 1.25rem;
  }

  .minimal-template__column {
    gap: 1.25rem;
  }

  .minimal-template__metric {
    justify-content: center;
    text-align: center;
    flex-wrap: wrap;
  }
}
</style>
