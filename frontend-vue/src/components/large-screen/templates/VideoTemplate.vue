<script setup lang="ts">
import { computed, onErrorCaptured, defineAsyncComponent } from 'vue'
import { X } from 'lucide-vue-next'
import type { LargeScreenConfig } from '../composables/useLargeScreenData'

// 异步加载视频播放器，避免同步导入导致模板整个崩溃
const RTSPVideoPlayer = defineAsyncComponent(() => import('@/components/video/RTSPVideoPlayer.vue'))

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

onErrorCaptured((err, instance, info) => {
  console.error('[VideoTemplate] 错误:', err, info)
  return false
})

// 取第一个在线设备作为视频源
const videoDevice = computed(() => {
  return props.devices.find(d => d.status === 'online') || props.devices[0] || null
})

// 指标卡片颜色循环
const cardColorClasses = ['--cyan', '--green', '--blue', '--orange', '--purple', '--pink', '--yellow', '--teal']

function cardColorClass(idx: number): string {
  return `video-template__metric-card${cardColorClasses[idx % cardColorClasses.length]}`
}

// 预处理指标列表：前两个为并排（文字上数字下居中），其余为独立行（文字左数字中）
const metricRows = computed(() => {
  const keys = props.config.metrics || []
  const rows: { keys: string[]; isSideBySide: boolean }[] = []
  for (let i = 0; i < keys.length; i++) {
    if (i < 2) {
      // 前两个：每两个一组并排
      if (i % 2 === 0) {
        rows.push({ keys: [keys[i]], isSideBySide: true })
      } else {
        // 追加到最后一组
        if (rows.length > 0) rows[rows.length - 1].keys.push(keys[i])
      }
    } else {
      // 第三个及以后：每个独占一行
      rows.push({ keys: [keys[i]], isSideBySide: false })
    }
  }
  return rows
})

// 格式化时钟
const timeText = computed(() => {
  const now = new Date()
  const weekDays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  const date = `${now.getFullYear()}年${String(now.getMonth() + 1).padStart(2, '0')}月${String(now.getDate()).padStart(2, '0')}日`
  const time = now.toLocaleTimeString('zh-CN', { hour12: false })
  return `${date} ${weekDays[now.getDay()]} ${time}`
})
</script>

<template>
  <div class="video-template relative z-10 h-full w-full overflow-hidden">
    <!-- 背景 -->
    <div class="video-template__bg" />

    <!-- 顶部装饰线 -->
    <div class="video-template__top-line" />

    <!-- Logo （左上角，从系统设置中获取） -->
    <div class="video-template__logo-area">
      <img
        v-if="storeLogo"
        :src="storeLogo"
        alt="Logo"
        class="video-template__logo"
      />
    </div>

    <!-- 关闭按钮 -->
    <button
      class="video-template__close"
      @click="emit('close')"
    >
      <X class="w-5 h-5" />
    </button>

    <!-- 主要内容区域 -->
    <div class="video-template__main">
      <!-- 左侧：标题 + 指标 -->
      <div class="video-template__left">
        <!-- 标题 -->
        <h1 class="video-template__title">
          {{ config.title || '客流统计大屏' }}
        </h1>

        <!-- 分割线 -->
        <div class="video-template__divider" />

        <!-- 当前时间 -->
        <div class="video-template__time">
          {{ timeText }}
        </div>

        <!-- 指标卡片（从通用配置动态获取） -->
        <div class="video-template__metrics">
          <div
            v-for="(row, ri) in metricRows"
            :key="ri"
            class="video-template__metrics-row"
            :class="{ 'video-template__metrics-row--split': row.isSideBySide }"
          >
            <div
              v-for="(key, ki) in row.keys"
              :key="key"
              class="video-template__metric-card"
              :class="[
                row.isSideBySide ? '' : 'video-template__metric-card--standalone',
                cardColorClass(ri * 2 + ki)
              ]"
            >
              <div class="video-template__metric-body">
                <span class="video-template__metric-label">{{ getLabel(key) }}</span>
                <span class="video-template__metric-value">
                  {{ loading ? '---' : (metrics[key] ?? 0) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：实时视频 -->
      <div class="video-template__right">
        <div class="video-template__video-wrapper">
          <div class="video-template__video-header">
            <span class="video-template__video-dot" />
            <span class="video-template__video-title">
              {{ videoDevice ? videoDevice.name : '实时监控' }}
            </span>
          </div>
          <div class="video-template__video-body">
            <RTSPVideoPlayer
              v-if="videoDevice"
              :device-id="videoDevice.id"
              :name="videoDevice.name"
              :status="videoDevice.status"
              :auto-play="true"
              :compact="false"
              :show-controls="false"
              class="w-full h-full"
            />
            <div
              v-else
              class="w-full h-full flex items-center justify-center text-[#8892a0] text-lg"
            >
              暂无可用视频设备
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.video-template {
  color: #e0e6ed;
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
}

.video-template__bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 20% 50%, rgba(0, 120, 255, 0.08) 0%, transparent 60%),
    radial-gradient(ellipse at 80% 50%, rgba(0, 200, 255, 0.06) 0%, transparent 60%),
    linear-gradient(180deg, #0a1628 0%, #0d1f3c 50%, #091525 100%);
}

.video-template__top-line {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent 0%, #00aaff 20%, #00d4ff 50%, #00aaff 80%, transparent 100%);
}

.video-template__logo-area {
  position: absolute;
  top: 20px;
  left: 48px;
  z-index: 20;
}

.video-template__logo {
  max-height: 50px;
  max-width: 180px;
  object-fit: contain;
}

.video-template__close {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 20;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #8892a0;
  cursor: pointer;
  transition: all 0.2s ease;
}

.video-template__close:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #e0e6ed;
}

.video-template__main {
  position: relative;
  z-index: 10;
  display: flex;
  height: 100%;
  padding: 64px 48px 48px;
  gap: 32px;
}

/* 左侧 */
.video-template__left {
  flex: 2;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 24px;
}

.video-template__title {
  margin: 0;
  font-size: clamp(2.4rem, 3.5vw, 3.8rem);
  font-weight: 700;
  color: #f0f4ff;
  letter-spacing: 0.04em;
  text-shadow: 0 2px 12px rgba(0, 120, 255, 0.15);
  text-align: center;
}

.video-template__divider {
  width: 60%;
  max-width: 320px;
  height: 2px;
  margin: 12px auto;
  border-radius: 2px;
  background: linear-gradient(90deg, transparent, rgba(0, 200, 255, 0.6), rgba(0, 220, 255, 0.8), rgba(0, 200, 255, 0.6), transparent);
}

.video-template__time {
  font-size: clamp(1rem, 1.4vw, 1.4rem);
  color: #8892a0;
  letter-spacing: 0.02em;
  text-align: center;
}

/* 指标卡片 */
.video-template__metrics {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.video-template__metrics-row {
  display: flex;
  gap: 16px;
}

.video-template__metrics-row .video-template__metric-card {
  flex: 1;
  min-width: 0;
}

.video-template__metric-card {
  display: flex;
  align-items: center;
  padding: 20px 24px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  transition: all 0.2s ease;
}

.video-template__metric-card--cyan {
  background: linear-gradient(135deg, rgba(0, 217, 255, 0.12), rgba(0, 217, 255, 0.04));
  border-color: rgba(0, 217, 255, 0.2);
}

.video-template__metric-card--green {
  background: linear-gradient(135deg, rgba(0, 255, 136, 0.12), rgba(0, 255, 136, 0.04));
  border-color: rgba(0, 255, 136, 0.2);
}

.video-template__metric-card--blue {
  background: linear-gradient(135deg, rgba(74, 158, 255, 0.12), rgba(74, 158, 255, 0.04));
  border-color: rgba(74, 158, 255, 0.2);
}

.video-template__metric-card--orange {
  background: linear-gradient(135deg, rgba(255, 149, 0, 0.12), rgba(255, 149, 0, 0.04));
  border-color: rgba(255, 149, 0, 0.2);
}

.video-template__metric-card--purple {
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.12), rgba(168, 85, 247, 0.04));
  border-color: rgba(168, 85, 247, 0.2);
}

.video-template__metric-card--pink {
  background: linear-gradient(135deg, rgba(244, 63, 94, 0.12), rgba(244, 63, 94, 0.04));
  border-color: rgba(244, 63, 94, 0.2);
}

.video-template__metric-card--yellow {
  background: linear-gradient(135deg, rgba(255, 185, 0, 0.12), rgba(255, 185, 0, 0.04));
  border-color: rgba(255, 185, 0, 0.2);
}

.video-template__metric-card--teal {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(16, 185, 129, 0.04));
  border-color: rgba(16, 185, 129, 0.2);
}

.video-template__metric-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  gap: 6px;
  min-width: 0;
}

.video-template__metric-card--standalone .video-template__metric-body {
  flex-direction: row;
}

.video-template__metric-label {
  font-size: clamp(1rem, 1.4vw, 1.4rem);
  font-weight: 700;
  color: #8892a0;
  text-align: center;
  flex-shrink: 0;
}

.video-template__metric-card--standalone .video-template__metric-label {
  white-space: nowrap;
}

.video-template__metric-value {
  font-size: clamp(2.2rem, 3.2vw, 3.6rem);
  font-weight: 700;
  color: #f0f4ff;
  font-variant-numeric: tabular-nums;
  text-align: center;
}

.video-template__metric-card--standalone .video-template__metric-value {
  flex: 1;
}

/* 右侧 */
.video-template__right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
}

.video-template__video-wrapper {
  width: 100%;
  max-width: 640px;
  aspect-ratio: 4 / 3;
  border-radius: 16px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
}

.video-template__video-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  background: rgba(0, 0, 0, 0.3);
  flex-shrink: 0;
}

.video-template__video-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #00ff88;
  box-shadow: 0 0 8px rgba(0, 255, 136, 0.5);
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.video-template__video-title {
  font-size: clamp(0.9rem, 1.2vw, 1.1rem);
  font-weight: 600;
  color: #e0e6ed;
}

.video-template__video-body {
  flex: 1;
  min-height: 0;
}

/* 响应式 - 小屏堆叠 */
@media (max-width: 900px) {
  .video-template__main {
    flex-direction: column;
    padding: 56px 24px 24px;
    gap: 20px;
  }

  .video-template__left {
    flex: none;
    width: 100%;
  }

  .video-template__right {
    flex: 1;
    min-height: 300px;
  }

  .video-template__logo-area {
    left: 24px;
  }

  .video-template__logo {
    max-height: 36px;
  }
}

@media (max-width: 600px) {
  .video-template__main {
    padding: 48px 16px 16px;
    gap: 16px;
  }

  .video-template__logo-area {
    top: 12px;
    right: 48px;
  }

  .video-template__logo {
    max-height: 36px;
  }

  .video-template__metric-card {
    padding: 14px 16px;
  }

  .video-template__metric-value {
    font-size: 1.5rem;
  }
}
</style>
