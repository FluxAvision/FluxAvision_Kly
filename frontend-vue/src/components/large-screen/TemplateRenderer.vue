<script setup lang="ts">
/**
 * 模板渲染引擎
 * 根据 JSON 配置动态渲染模板组件
 * 大屏模式：画布100%平铺满整个浏览器（拉伸填满，不保持比例）
 */
import { computed, defineAsyncComponent, ref, onMounted, onUnmounted } from 'vue'
import type { TemplateConfig, ComponentConfig, ComponentStyles } from '@/types/template-editor'
import { useLargeScreenData } from '@/components/large-screen/composables/useLargeScreenData'

// 动态加载组件
const componentMap: Record<string, any> = {
  'border': defineAsyncComponent(() => import('@/components/template-editor/widgets/DataVBorder.vue')),
  'decoration': defineAsyncComponent(() => import('@/components/template-editor/widgets/DataVDecoration.vue')),
  'metric-card': defineAsyncComponent(() => import('@/components/template-editor/widgets/MetricCard.vue')),
  'counter': defineAsyncComponent(() => import('@/components/template-editor/widgets/DigitalCounter.vue')),
  'chart-line': defineAsyncComponent(() => import('@/components/template-editor/widgets/ChartLine.vue')),
  'chart-bar': defineAsyncComponent(() => import('@/components/template-editor/widgets/ChartBar.vue')),
  'video': defineAsyncComponent(() => import('@/components/template-editor/widgets/VideoPlayer.vue')),
  'title': defineAsyncComponent(() => import('@/components/template-editor/widgets/TitleText.vue')),
  'text': defineAsyncComponent(() => import('@/components/template-editor/widgets/TitleText.vue')),
  'clock': defineAsyncComponent(() => import('@/components/template-editor/widgets/ClockWidget.vue')),
}

const props = defineProps<{
  config: TemplateConfig
}>()

const data = useLargeScreenData()

// 容器引用
const containerRef = ref<HTMLElement | null>(null)
const containerSize = ref({ width: 0, height: 0 })

// 缩放比例 - 等比缩放（取最小值，确保内容完整显示）
const scale = computed(() => {
  if (containerSize.value.width === 0 || containerSize.value.height === 0) return 1
  const sx = containerSize.value.width / props.config.canvas.width
  const sy = containerSize.value.height / props.config.canvas.height
  return Math.min(sx, sy)
})

// 容器背景样式 - 铺满全屏，不受画布缩放影响
const containerStyle = computed(() => ({
  backgroundColor: props.config.canvas.backgroundImage
    ? undefined
    : (props.config.canvas.backgroundColor || '#0a192f'),
  backgroundImage: props.config.canvas.backgroundImage
    ? `url(${props.config.canvas.backgroundImage})`
    : undefined,
  backgroundSize: 'cover',
  backgroundPosition: 'center',
}))

// 计算画布样式 - 等比缩放+居中定位（不含背景）
const canvasStyle = computed(() => ({
  position: 'absolute',
  left: '50%',
  top: '50%',
  transform: `translate(-50%, -50%) scale(${scale.value})`,
  transformOrigin: 'center center',
  width: `${props.config.canvas.width}px`,
  height: `${props.config.canvas.height}px`,
}))

// 排序后的组件列表
const sortedComponents = computed(() => {
  return [...props.config.components]
    .filter(c => c.visible)
    .sort((a, b) => a.zIndex - b.zIndex)
})

// 组件数据映射 - 使用 computed 确保响应式
const componentDataMap = computed(() => {
  const map: Record<string, any> = {}

  for (const comp of sortedComponents.value) {
    // 如果没有 dataSource 或 dataSource 为空对象，根据组件类型提供默认数据
    if (!comp.dataSource || Object.keys(comp.dataSource).length === 0) {
      if (comp.type === 'metric-card' || comp.type === 'counter') {
        // 默认绑定第一个指标
        map[comp.id] = {
          value: data.metrics.value['todayIn'] || 0,
          label: data.getLabel('todayIn'),
        }
      } else if (comp.type === 'chart-line' || comp.type === 'chart-bar') {
        map[comp.id] = { hourlyData: data.hourlyData.value }
      } else {
        map[comp.id] = {}
      }
      continue
    }

    const { type, key } = comp.dataSource

    // 如果 type 缺失但有 key，根据 key 推断类型
    if (!type && key) {
      // 如果 key 是指标名称，则类型为 metric
      const metricKeys = ['todayIn', 'todayOut', 'currentIn', 'weekIn', 'weekOut', 'monthIn', 'monthOut', 'totalIn', 'totalOut']
      if (metricKeys.includes(key)) {
        map[comp.id] = {
          value: data.metrics.value[key] || 0,
          label: data.getLabel(key),
        }
        continue
      }
    }

    switch (type) {
      case 'metric':
        map[comp.id] = {
          value: data.metrics.value[key || ''] || 0,
          label: data.getLabel(key || ''),
        }
        break
      case 'device':
        map[comp.id] = { device: data.allDevices.value.find(d => d.id === key) }
        break
      case 'hourly':
        map[comp.id] = { hourlyData: data.hourlyData.value }
        break
      default:
        // 默认处理：如果组件类型是指标相关，尝试使用 key 获取数据
        if ((comp.type === 'metric-card' || comp.type === 'counter') && key) {
          map[comp.id] = {
            value: data.metrics.value[key] || 0,
            label: data.getLabel(key),
          }
        } else if (comp.type === 'chart-line' || comp.type === 'chart-bar') {
          map[comp.id] = { hourlyData: data.hourlyData.value }
        } else {
          map[comp.id] = {}
        }
    }
  }

  return map
})

// 获取组件数据
function getComponentData(component: ComponentConfig) {
  return componentDataMap.value[component.id] || {}
}

// 计算组件样式
function getComponentStyle(comp: ComponentConfig) {
  const style: Record<string, any> = {
    position: 'absolute',
    left: `${comp.x}px`,
    top: `${comp.y}px`,
    width: `${comp.width}px`,
    height: `${comp.height}px`,
    zIndex: comp.zIndex,
    opacity: comp.opacity,
    transform: `rotate(${comp.rotation}deg)`,
  }

  // 合并自定义样式
  if (comp.styles) {
    const s: ComponentStyles = comp.styles
    if (s.backgroundColor) style.backgroundColor = s.backgroundColor
    if (s.borderColor) style.borderColor = s.borderColor
    if (s.borderWidth) style.borderWidth = `${s.borderWidth}px`
    if (s.borderRadius) style.borderRadius = `${s.borderRadius}px`
    if (s.padding) style.padding = `${s.padding}px`
    if (s.boxShadow) style.boxShadow = s.boxShadow
  }

  return style
}

// 更新容器尺寸
function updateContainerSize() {
  if (containerRef.value) {
    containerSize.value = {
      width: containerRef.value.clientWidth,
      height: containerRef.value.clientHeight,
    }
  }
}

onMounted(() => {
  updateContainerSize()
  window.addEventListener('resize', updateContainerSize)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateContainerSize)
})
</script>

<template>
  <div ref="containerRef" class="template-renderer relative overflow-hidden w-full h-full" :style="containerStyle">
    <!-- 加载中 -->
    <div v-if="data.loading.value" class="absolute inset-0 flex items-center justify-center text-[#8892a0] text-sm">
      加载数据中...
    </div>

    <!-- 画布 -->
    <div v-else class="canvas-inner" :style="canvasStyle">
      <!-- 背景遮罩 -->
      <div
        v-if="config.canvas.backgroundImage"
        class="absolute inset-0 bg-black/30 pointer-events-none"
      />

      <!-- 渲染组件 -->
      <component
        v-for="comp in sortedComponents"
        :key="comp.id"
        :is="componentMap[comp.type]"
        :config="comp"
        :data="getComponentData(comp)"
        :style="getComponentStyle(comp)"
      />
    </div>
  </div>
</template>

<style scoped>
.canvas-inner {
  position: relative;
}
</style>
