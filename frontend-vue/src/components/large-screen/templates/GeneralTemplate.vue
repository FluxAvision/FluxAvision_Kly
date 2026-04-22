<script setup lang="ts">
import { computed } from 'vue'
import { X } from 'lucide-vue-next'
import { metricMap } from '../composables/useLargeScreenData'
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

const leftCards = computed(() => ([
  {
    key: 'todayIn',
    label: '进',
    value: props.metrics.todayIn || 0,
    color: metricMap.todayIn?.color || '#00d9ff',
  },
  {
    key: 'todayOut',
    label: '出',
    value: props.metrics.todayOut || 0,
    color: metricMap.todayOut?.color || '#00ff88',
  },
]))

const rightCards = computed(() => ([
  {
    key: 'instantaneousMaxCapacity',
    label: '瞬时最大承载人数',
    value: props.metrics.instantaneousMaxCapacity || 0,
    color: metricMap.instantaneousMaxCapacity?.color || '#f59e0b',
  },
  {
    key: 'storeMaxCapacity',
    label: '最大承载人数',
    value: props.metrics.storeMaxCapacity || 0,
    color: metricMap.storeMaxCapacity?.color || '#8b5cf6',
  },
]))

const centerCard = computed(() => ({
  key: 'currentIn',
  label: '当前在场人数',
  value: props.metrics.currentIn || 0,
  color: metricMap.currentIn?.color || '#4a9eff',
}))

const fallbackTitle = '欢迎参观'
const fallbackLogoText = '客'

const timeParts = computed(() => {
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
  const dateText = `${now.getFullYear()}年${String(now.getMonth() + 1).padStart(2, '0')}月${String(now.getDate()).padStart(2, '0')}日`
  const weekText = weekDays[now.getDay()]
  const timeText = now.toLocaleTimeString('zh-CN', { hour12: false })
  return { dateText, weekText, timeText }
})
</script>

<template>
  <div class="general-template relative z-10 h-full w-full overflow-hidden">
    <div class="general-template__overlay absolute inset-0" />

    <div class="relative z-10 flex h-full flex-col px-10 py-8">
      <div class="flex items-start justify-between">
        <div class="flex items-center gap-4">
          <div v-if="storeLogo" class="general-template__logo-shell">
            <img :src="storeLogo" alt="Logo" class="h-full w-full object-contain" />
          </div>
          <div v-else class="general-template__logo-shell general-template__logo-shell--placeholder">
            <span>{{ (config.title || fallbackLogoText).slice(0, 1) }}</span>
          </div>
        </div>

        <button
          class="general-template__close"
          @click="emit('close')"
        >
          <X class="h-5 w-5" />
        </button>
      </div>

      <div class="flex flex-1 flex-col items-center justify-center">
        <div class="w-full max-w-[1320px] text-center">
          <h1 class="general-template__title">
            {{ config.title || fallbackTitle }}
          </h1>
          <p v-if="config.subtitle" class="general-template__subtitle">
            {{ config.subtitle }}
          </p>

          <div class="general-template__time-row">
            <span>{{ timeParts.dateText }}</span>
            <span>{{ timeParts.weekText }}</span>
            <span>{{ timeParts.timeText }}</span>
          </div>

          <div class="general-template__metrics-grid">
            <div class="general-template__stack">
              <div
                v-for="card in leftCards"
                :key="card.key"
                class="general-template__mini-card"
              >
                <div class="general-template__mini-label">{{ card.label }}</div>
                <div class="general-template__mini-value" :style="{ color: card.color }">
                  {{ loading ? '--' : card.value.toLocaleString() }}
                </div>
              </div>
            </div>

            <div class="general-template__center-card">
              <div class="general-template__center-label">{{ centerCard.label }}</div>
              <div class="general-template__center-value" :style="{ color: centerCard.color }">
                {{ loading ? '--' : centerCard.value.toLocaleString() }}
              </div>
            </div>

            <div class="general-template__stack">
              <div
                v-for="card in rightCards"
                :key="card.key"
                class="general-template__mini-card"
              >
                <div class="general-template__mini-label">{{ card.label }}</div>
                <div class="general-template__mini-value" :style="{ color: card.color }">
                  {{ loading ? '--' : card.value.toLocaleString() }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.general-template {
  color: #d9fbff;
}

.general-template__overlay {
  background:
    linear-gradient(180deg, rgba(0, 0, 0, 0.44) 0%, rgba(1, 7, 18, 0.52) 100%),
    radial-gradient(circle at top center, rgba(98, 225, 255, 0.1) 0%, rgba(98, 225, 255, 0) 40%);
}

.general-template__logo-shell {
  display: flex;
  height: 84px;
  width: 84px;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  border: 1px solid rgba(180, 247, 255, 0.34);
  background: rgba(5, 19, 35, 0.52);
  box-shadow: 0 0 28px rgba(92, 220, 255, 0.18), inset 0 0 18px rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(10px);
  overflow: hidden;
}

.general-template__logo-shell--placeholder {
  color: #b8f6ff;
  font-size: 2rem;
  font-weight: 700;
}

.general-template__close {
  display: flex;
  height: 42px;
  width: 42px;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  border: 1px solid rgba(180, 247, 255, 0.28);
  background: rgba(6, 18, 34, 0.46);
  color: #d9fbff;
  transition: background-color 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
}

.general-template__close:hover {
  background: rgba(11, 31, 56, 0.7);
  border-color: rgba(180, 247, 255, 0.44);
  transform: translateY(-1px);
}

.general-template__title {
  margin: 0;
  font-size: clamp(2.6rem, 4.5vw, 5rem);
  font-weight: 800;
  line-height: 1.15;
  letter-spacing: 0.06em;
  color: #86eaff;
  text-shadow: 0 0 20px rgba(96, 226, 255, 0.38);
}

.general-template__subtitle {
  margin: 0.8rem 0 0;
  font-size: clamp(1rem, 1.2vw, 1.25rem);
  color: rgba(210, 249, 255, 0.82);
  letter-spacing: 0.08em;
}

.general-template__time-row {
  margin-top: 2rem;
  display: flex;
  justify-content: center;
  gap: clamp(1.5rem, 4vw, 4rem);
  color: #baf8ff;
  font-size: clamp(1rem, 1.2vw, 1.5rem);
  font-weight: 600;
  letter-spacing: 0.04em;
}

.general-template__metrics-grid {
  margin: 3rem auto 0;
  display: grid;
  width: min(100%, 1240px);
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1.5rem;
  align-items: stretch;
}

.general-template__stack {
  display: grid;
  gap: 1.5rem;
}

.general-template__mini-card,
.general-template__center-card {
  border: 1px solid rgba(150, 245, 255, 0.4);
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(10, 22, 36, 0.38) 0%, rgba(6, 14, 24, 0.52) 100%);
  box-shadow: inset 0 0 26px rgba(130, 236, 255, 0.08), 0 0 24px rgba(87, 213, 255, 0.1);
  backdrop-filter: blur(4px);
}

.general-template__mini-card {
  min-height: 170px;
  padding: 1.5rem 1.25rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.general-template__center-card {
  min-height: 356px;
  padding: 2rem 1.5rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.general-template__mini-label,
.general-template__center-label {
  color: #c7fbff;
  font-size: clamp(1rem, 1.1vw, 1.35rem);
  font-weight: 700;
  letter-spacing: 0.05em;
}

.general-template__mini-label {
  margin-bottom: 1rem;
}

.general-template__center-label {
  margin-bottom: 1.5rem;
  font-size: clamp(1.2rem, 1.4vw, 1.6rem);
}

.general-template__mini-value {
  font-size: clamp(2.6rem, 3vw, 3.8rem);
  line-height: 1;
  font-weight: 800;
  text-shadow: 0 0 16px rgba(134, 234, 255, 0.26);
}

.general-template__center-value {
  font-size: clamp(4rem, 6vw, 6.8rem);
  line-height: 1;
  font-weight: 800;
  text-shadow: 0 0 20px rgba(134, 234, 255, 0.26);
}

@media (max-width: 900px) {
  .general-template__logo-shell {
    height: 64px;
    width: 64px;
  }

  .general-template__time-row {
    flex-direction: column;
    gap: 0.7rem;
  }

  .general-template__metrics-grid {
    grid-template-columns: 1fr;
  }

  .general-template__center-card {
    min-height: 220px;
  }
}
</style>
