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

const fallbackTitle = '欢迎您'

const visitorDigits = computed(() => {
  const value = String(props.metrics.totalIn || 0)
  const padded = value.padStart(Math.max(6, value.length), '0')
  return padded.split('')
})

const summaryCards = computed(() => [
  { key: 'todayIn', title: '当日', value: props.metrics.todayIn || 0 },
  { key: 'monthIn', title: '本月', value: props.metrics.monthIn || 0 },
  { key: 'yearIn', title: '全年', value: props.metrics.yearIn || 0 },
])

const timeText = computed(() => {
  props.clockTime
  const now = new Date()
  const weekDays = [
    '星期日',
    '星期一',
    '星期二',
    '星期三',
    '星期四',
    '星期五',
    '星期六',
  ]
  const date = `${now.getFullYear()}年${String(now.getMonth() + 1).padStart(2, '0')}月${String(now.getDate()).padStart(2, '0')}日`
  const time = now.toLocaleTimeString('zh-CN', { hour12: false })
  return `${date}${weekDays[now.getDay()]} ${time}`
})
</script>

<template>
  <div class="standard-template relative z-10 h-full w-full overflow-hidden">
    <div class="standard-template__overlay absolute inset-0" />
    <div class="standard-template__mountains standard-template__mountains--left absolute left-0 bottom-0" />
    <div class="standard-template__mountains standard-template__mountains--right absolute right-0 bottom-0" />

    <div class="relative z-10 flex h-full flex-col px-10 py-8">
      <div class="flex justify-end">
        <button
          class="standard-template__close"
          @click="emit('close')"
        >
          <X class="h-5 w-5" />
        </button>
      </div>

      <div class="flex flex-1 flex-col items-center justify-center">
        <h1 class="standard-template__title">
          {{ config.title || fallbackTitle }}
        </h1>

        <div class="standard-template__hero">
          <div class="standard-template__hero-prefix">您是第</div>
          <div class="standard-template__digit-row">
            <span
              v-for="(digit, index) in visitorDigits"
              :key="`${digit}-${index}`"
              class="standard-template__digit"
            >
              {{ loading ? '-' : digit }}
            </span>
          </div>
          <div class="standard-template__hero-suffix">位来访者</div>
        </div>

        <div class="standard-template__time">
          {{ timeText }}
        </div>

        <div class="standard-template__summary-grid">
          <div
            v-for="card in summaryCards"
            :key="card.key"
            class="standard-template__summary-card"
          >
            <div class="standard-template__summary-title">{{ card.title }}</div>
            <div class="standard-template__summary-content">
              <div class="standard-template__summary-digits">
                <span
                  v-for="(digit, index) in String(card.value).padStart(6, '0').split('')"
                  :key="`${card.key}-${digit}-${index}`"
                  class="standard-template__summary-digit"
                >
                  {{ loading ? '-' : digit }}
                </span>
              </div>
              <span class="standard-template__summary-unit">人次</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.standard-template {
  color: #fff7f7;
}

.standard-template__overlay {
  background:
    linear-gradient(180deg, rgba(229, 28, 66, 0.2) 0%, rgba(255, 89, 89, 0.1) 38%, rgba(123, 12, 23, 0.18) 100%),
    linear-gradient(180deg, rgba(255, 93, 109, 0.18), rgba(255, 93, 109, 0.1));
}

.standard-template__mountains {
  width: 30vw;
  min-width: 260px;
  height: 42vh;
  opacity: 0.2;
  pointer-events: none;
}

.standard-template__mountains--left {
  background:
    radial-gradient(circle at 20% 100%, rgba(255, 255, 255, 0.2) 0 2px, transparent 2px),
    linear-gradient(180deg, transparent 30%, rgba(145, 17, 35, 0.3) 100%);
  clip-path: polygon(0% 100%, 0% 56%, 12% 48%, 22% 55%, 31% 40%, 46% 46%, 57% 32%, 72% 50%, 83% 42%, 100% 60%, 100% 100%);
}

.standard-template__mountains--right {
  background:
    radial-gradient(circle at 80% 100%, rgba(255, 255, 255, 0.2) 0 2px, transparent 2px),
    linear-gradient(180deg, transparent 30%, rgba(145, 17, 35, 0.3) 100%);
  clip-path: polygon(0% 100%, 0% 60%, 16% 43%, 27% 51%, 40% 34%, 54% 42%, 70% 30%, 83% 48%, 100% 40%, 100% 100%);
}

.standard-template__close {
  display: flex;
  height: 42px;
  width: 42px;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  border: 1px solid rgba(255, 255, 255, 0.24);
  background: rgba(139, 16, 31, 0.28);
  color: #fff7f7;
  transition: transform 0.2s ease, background-color 0.2s ease;
}

.standard-template__close:hover {
  transform: translateY(-1px);
  background: rgba(139, 16, 31, 0.5);
}

.standard-template__title {
  margin: 0;
  text-align: center;
  font-size: clamp(3.2rem, 5vw, 5.6rem);
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #fff9f3;
  text-shadow: 0 4px 12px rgba(136, 14, 33, 0.2);
}

.standard-template__hero {
  margin-top: 3rem;
  display: flex;
  align-items: end;
  justify-content: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.standard-template__hero-prefix,
.standard-template__hero-suffix {
  margin-bottom: 0.35rem;
  font-size: clamp(2rem, 3vw, 3.6rem);
  font-weight: 700;
  color: #fff7f2;
  text-shadow: 0 2px 8px rgba(136, 14, 33, 0.18);
}

.standard-template__digit-row {
  display: flex;
  gap: 1rem;
}

.standard-template__digit {
  display: flex;
  width: clamp(4rem, 5vw, 5.7rem);
  height: clamp(6rem, 7vw, 7.9rem);
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: rgba(255, 252, 252, 0.96);
  color: #e12c53;
  font-size: clamp(3.8rem, 5vw, 5.6rem);
  font-weight: 700;
  box-shadow: 0 10px 24px rgba(152, 20, 37, 0.12);
}

.standard-template__time {
  margin-top: 2rem;
  min-width: min(100%, 760px);
  padding: 0.5rem 2rem;
  text-align: center;
  font-size: clamp(1.7rem, 2.2vw, 2.8rem);
  color: #d92c4f;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0) 0%, rgba(255, 246, 246, 0.92) 12%, rgba(255, 246, 246, 0.92) 88%, rgba(255, 255, 255, 0) 100%);
}

.standard-template__summary-grid {
  margin-top: 5rem;
  display: grid;
  width: min(100%, 1420px);
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 3rem;
}

.standard-template__summary-card {
  padding: 1.4rem 1.6rem 1.25rem;
  border-radius: 10px;
  background: rgba(67, 20, 17, 0.62);
  box-shadow: 0 14px 30px rgba(81, 9, 16, 0.12);
}

.standard-template__summary-title {
  margin-bottom: 1rem;
  font-size: clamp(1.6rem, 2vw, 2.4rem);
  font-weight: 700;
  color: #fff7f2;
}

.standard-template__summary-content {
  display: flex;
  align-items: flex-end;
  justify-content: flex-start;
  gap: 0.5rem;
  flex-wrap: nowrap;
}

.standard-template__summary-digits {
  display: flex;
  gap: 0.45rem;
}

.standard-template__summary-digit {
  display: flex;
  width: clamp(2.8rem, 2.7vw, 3.9rem);
  height: clamp(4rem, 4vw, 4.9rem);
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: rgba(255, 252, 252, 0.96);
  color: #e12c53;
  font-size: clamp(2rem, 2.1vw, 3.1rem);
  font-weight: 700;
}

.standard-template__summary-unit {
  flex-shrink: 0;
  white-space: nowrap;
  font-size: clamp(1.4rem, 1vw, 2rem);
  font-weight: 700;
  color: #fff7f2;
}

@media (max-width: 1100px) {
  .standard-template__summary-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
}

@media (max-width: 900px) {
  .standard-template__hero {
    gap: 0.75rem;
  }

  .standard-template__digit-row {
    gap: 0.55rem;
  }

  .standard-template__time {
    min-width: 100%;
  }
}
</style>
