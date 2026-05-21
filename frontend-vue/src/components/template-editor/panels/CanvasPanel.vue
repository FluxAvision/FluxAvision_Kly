<script setup lang="ts">
/**
 * 画布面板 - 支持组件拖拽、选择、调整大小
 * 画布按比例缩放平铺内容区域，实时渲染组件效果
 * 支持缩放控制
 */
import { ref, computed, onMounted, onUnmounted, defineAsyncComponent, watch } from 'vue'
import type { ComponentConfig, CanvasConfig, ComponentStyles } from '@/types/template-editor'
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
  components: ComponentConfig[]
  canvasConfig: CanvasConfig
  selectedId: string | null
}>()

const emit = defineEmits<{
  select: [component: ComponentConfig | null]
  move: [id: string, position: { x: number; y: number }]
  resize: [id: string, size: { width: number; height: number }, position?: { x: number; y: number }]
  updateCanvas: [updates: { width?: number; height?: number }]
}>()

const data = useLargeScreenData()

const containerRef = ref<HTMLElement | null>(null)
const canvasRef = ref<HTMLElement | null>(null)

// 缩放级别（100% = 1, 50% = 0.5, 200% = 2）
const zoomLevel = ref(1)
const minZoom = 0.25
const maxZoom = 2

// 容器尺寸
const containerSize = ref({ width: 0, height: 0 })

// 自动计算的缩放比例（填满容器）
const autoScale = computed(() => {
  if (containerSize.value.width === 0) return 1
  const scaleX = containerSize.value.width / props.canvasConfig.width
  const scaleY = containerSize.value.height / props.canvasConfig.height
  return Math.min(scaleX, scaleY)
})

// 实际缩放比例 = 自动缩放 * 用户缩放
const scale = computed(() => autoScale.value * zoomLevel.value)

// 拖拽状态
const isDragging = ref(false)
const dragComponentId = ref<string | null>(null)
const dragOffset = ref({ x: 0, y: 0 })

// 调整大小状态
const isResizing = ref(false)
const resizeComponentId = ref<string | null>(null)
const resizeStartPos = ref({ x: 0, y: 0 })
const resizeStartSize = ref({ width: 0, height: 0 })
const resizeStartComponentPos = ref({ x: 0, y: 0 })
const resizeHandle = ref<string | null>(null)

// 更新容器尺寸
function updateContainerSize() {
  if (containerRef.value) {
    containerSize.value = {
      width: containerRef.value.clientWidth,
      height: containerRef.value.clientHeight,
    }
  }
}

// 缩放控制
function zoomIn() {
  zoomLevel.value = Math.min(maxZoom, zoomLevel.value + 0.1)
}

function zoomOut() {
  zoomLevel.value = Math.max(minZoom, zoomLevel.value - 0.1)
}

function resetZoom() {
  zoomLevel.value = 1
}

// 计算画布样式
const canvasStyle = computed(() => ({
  width: `${props.canvasConfig.width}px`,
  height: `${props.canvasConfig.height}px`,
  backgroundColor: props.canvasConfig.backgroundColor,
  backgroundImage: props.canvasConfig.backgroundImage
    ? `url(${props.canvasConfig.backgroundImage})`
    : undefined,
  backgroundSize: 'cover',
  backgroundPosition: 'center',
  transform: `scale(${scale.value})`,
  transformOrigin: 'top left',
}))

// 排序后的组件
const sortedComponents = computed(() => {
  return [...props.components].sort((a, b) => a.zIndex - b.zIndex)
})

// 组件数据映射
const componentDataMap = computed(() => {
  const map: Record<string, any> = {}

  for (const comp of sortedComponents.value) {
    if (!comp.dataSource || Object.keys(comp.dataSource).length === 0) {
      if (comp.type === 'metric-card' || comp.type === 'counter') {
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

    if (!type && key) {
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
    opacity: comp.visible ? comp.opacity : 0.3,
    transform: `rotate(${comp.rotation}deg)`,
  }

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

// 鼠标事件处理
function handleMouseDown(e: MouseEvent, component: ComponentConfig) {
  if (component.locked) return

  e.stopPropagation()
  emit('select', component)

  isDragging.value = true
  dragComponentId.value = component.id
  // 计算相对于画布的偏移（考虑缩放）
  const canvasRect = canvasRef.value?.getBoundingClientRect()
  if (canvasRect) {
    dragOffset.value = {
      x: e.clientX - canvasRect.left - component.x * scale.value,
      y: e.clientY - canvasRect.top - component.y * scale.value,
    }
  }
}

function handleMouseMove(e: MouseEvent) {
  const canvasRect = canvasRef.value?.getBoundingClientRect()
  if (!canvasRect) return

  if (isDragging.value && dragComponentId.value) {
    // 转换为画布坐标系
    const x = (e.clientX - canvasRect.left - dragOffset.value.x) / scale.value
    const y = (e.clientY - canvasRect.top - dragOffset.value.y) / scale.value
    emit('move', dragComponentId.value, { x, y })
  }

  if (isResizing.value && resizeComponentId.value) {
    // 转换为画布坐标系
    const deltaX = (e.clientX - resizeStartPos.value.x) / scale.value
    const deltaY = (e.clientY - resizeStartPos.value.y) / scale.value

    let newWidth = resizeStartSize.value.width
    let newHeight = resizeStartSize.value.height
    let newX = resizeStartComponentPos.value.x
    let newY = resizeStartComponentPos.value.y

    if (resizeHandle.value?.includes('e')) {
      newWidth = Math.max(50, resizeStartSize.value.width + deltaX)
    }
    if (resizeHandle.value?.includes('w')) {
      const diff = Math.min(deltaX, resizeStartSize.value.width - 50)
      newWidth = resizeStartSize.value.width - diff
      newX = resizeStartComponentPos.value.x + diff
    }
    if (resizeHandle.value?.includes('s')) {
      newHeight = Math.max(30, resizeStartSize.value.height + deltaY)
    }
    if (resizeHandle.value?.includes('n')) {
      const diff = Math.min(deltaY, resizeStartSize.value.height - 30)
      newHeight = resizeStartSize.value.height - diff
      newY = resizeStartComponentPos.value.y + diff
    }

    emit('resize', resizeComponentId.value, { width: newWidth, height: newHeight }, { x: newX, y: newY })
  }
}

function handleMouseUp() {
  isDragging.value = false
  dragComponentId.value = null
  isResizing.value = false
  resizeComponentId.value = null
  resizeHandle.value = null
}

// 调整大小手柄事件
function handleResizeStart(e: MouseEvent, componentId: string, handle: string) {
  e.stopPropagation()
  e.preventDefault()

  const component = props.components.find(c => c.id === componentId)
  if (!component || component.locked) return

  isResizing.value = true
  resizeComponentId.value = componentId
  resizeStartPos.value = { x: e.clientX, y: e.clientY }
  resizeStartSize.value = { width: component.width, height: component.height }
  resizeStartComponentPos.value = { x: component.x, y: component.y }
  resizeHandle.value = handle
}

// 点击画布空白区域取消选择
function handleCanvasClick(e: MouseEvent) {
  if (e.target === canvasRef.value) {
    emit('select', null)
  }
}

// 滚轮缩放
function handleWheel(e: WheelEvent) {
  if (e.ctrlKey || e.metaKey) {
    e.preventDefault()
    if (e.deltaY < 0) {
      zoomIn()
    } else {
      zoomOut()
    }
  }
}

// 键盘快捷键
function handleKeydown(e: KeyboardEvent) {
  if (e.ctrlKey || e.metaKey) {
    if (e.key === '=' || e.key === '+') {
      e.preventDefault()
      zoomIn()
    } else if (e.key === '-') {
      e.preventDefault()
      zoomOut()
    } else if (e.key === '0') {
      e.preventDefault()
      resetZoom()
    }
  }
}

onMounted(() => {
  updateContainerSize()
  window.addEventListener('resize', updateContainerSize)
  window.addEventListener('mousemove', handleMouseMove)
  window.addEventListener('mouseup', handleMouseUp)
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateContainerSize)
  window.removeEventListener('mousemove', handleMouseMove)
  window.removeEventListener('mouseup', handleMouseUp)
  window.removeEventListener('keydown', handleKeydown)
})

// 屏幕分辨率预设
const screenPresets = [
  { label: '自定义', width: 0, height: 0 },
  { label: '1920x1080', width: 1920, height: 1080 },
  { label: '2560x1440', width: 2560, height: 1440 },
  { label: '3840x2160', width: 3840, height: 2160 },
]

const selectedPreset = ref('')

// 切换屏幕预设
function handlePresetChange(label: string) {
  selectedPreset.value = label
  const preset = screenPresets.find(p => p.label === label)
  if (preset && preset.width > 0) {
    emit('updateCanvas', { width: preset.width, height: preset.height })
  }
}

// 暴露缩放方法给父组件
defineExpose({
  zoomIn,
  zoomOut,
  resetZoom,
  zoomLevel: computed(() => Math.round(zoomLevel.value * 100)),
})
</script>

<template>
  <div
    ref="containerRef"
    class="canvas-panel h-full overflow-auto bg-[#0d1421] relative"
    @wheel="handleWheel"
  >
    <!-- 缩放控制 -->
    <div class="absolute top-2 right-2 z-50 flex items-center gap-1 bg-[#1e293b] rounded px-2 py-1">
      <button
        class="w-6 h-6 flex items-center justify-center text-white/70 hover:text-white hover:bg-white/10 rounded transition-colors"
        @click="zoomOut"
        title="缩小 (Ctrl+-)"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line></svg>
      </button>
      <span class="text-xs text-white/70 w-10 text-center">{{ Math.round(zoomLevel * 100) }}%</span>
      <button
        class="w-6 h-6 flex items-center justify-center text-white/70 hover:text-white hover:bg-white/10 rounded transition-colors"
        @click="zoomIn"
        title="放大 (Ctrl++)"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
      </button>
      <button
        class="w-6 h-6 flex items-center justify-center text-white/70 hover:text-white hover:bg-white/10 rounded transition-colors"
        @click="resetZoom"
        title="重置 (Ctrl+0)"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>
      </button>
      <div class="h-4 w-px bg-[#1e293b] mx-1" />
      <select
        :value="selectedPreset"
        class="bg-[#0a192f] border border-[#1e293b] rounded text-xs text-white px-1.5 py-1 w-auto"
        @change="(e) => handlePresetChange((e.target as HTMLSelectElement).value)"
      >
        <option v-for="preset in screenPresets" :key="preset.label" :value="preset.label">{{ preset.label }}</option>
      </select>
    </div>

    <!-- 画布容器 - 居中显示 -->
    <div class="min-h-full flex items-start justify-center p-4" :style="{ minHeight: `${canvasConfig.height * scale + 32}px` }">
      <div
        ref="canvasRef"
        class="relative shadow-2xl"
        :style="canvasStyle"
        @click="handleCanvasClick"
      >
        <!-- 背景遮罩 -->
        <div
          v-if="canvasConfig.backgroundImage"
          class="absolute inset-0 bg-black/30 pointer-events-none"
        />

        <!-- 网格 - pointer-events-none 确保不影响拖拽 -->
        <div
          v-if="canvasConfig.grid.enabled"
          class="absolute inset-0 pointer-events-none"
          :style="{
            backgroundImage: `linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)`,
            backgroundSize: `${canvasConfig.grid.size}px ${canvasConfig.grid.size}px`,
          }"
        />

        <!-- 渲染组件 -->
        <div
          v-for="comp in sortedComponents"
          :key="comp.id"
          class="absolute select-none"
          :class="[
            comp.locked ? 'cursor-not-allowed' : 'cursor-move',
            selectedId === comp.id ? 'ring-2 ring-[#00d9ff]' : '',
          ]"
          :style="getComponentStyle(comp)"
          @mousedown="(e) => handleMouseDown(e, comp)"
        >
          <!-- 实时渲染组件 -->
          <component
            :is="componentMap[comp.type]"
            :config="comp"
            :data="getComponentData(comp)"
            class="w-full h-full"
          />

          <!-- 调整大小手柄 -->
          <template v-if="selectedId === comp.id && !comp.locked">
            <!-- 四角 -->
            <div
              class="absolute -top-1.5 -left-1.5 w-3 h-3 bg-[#00d9ff] cursor-nw-resize rounded-sm z-50"
              @mousedown="(e) => handleResizeStart(e, comp.id, 'nw')"
            />
            <div
              class="absolute -top-1.5 -right-1.5 w-3 h-3 bg-[#00d9ff] cursor-ne-resize rounded-sm z-50"
              @mousedown="(e) => handleResizeStart(e, comp.id, 'ne')"
            />
            <div
              class="absolute -bottom-1.5 -left-1.5 w-3 h-3 bg-[#00d9ff] cursor-sw-resize rounded-sm z-50"
              @mousedown="(e) => handleResizeStart(e, comp.id, 'sw')"
            />
            <div
              class="absolute -bottom-1.5 -right-1.5 w-3 h-3 bg-[#00d9ff] cursor-se-resize rounded-sm z-50"
              @mousedown="(e) => handleResizeStart(e, comp.id, 'se')"
            />
            <!-- 四边 -->
            <div
              class="absolute -top-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-[#00d9ff] cursor-n-resize rounded-sm z-50"
              @mousedown="(e) => handleResizeStart(e, comp.id, 'n')"
            />
            <div
              class="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-[#00d9ff] cursor-s-resize rounded-sm z-50"
              @mousedown="(e) => handleResizeStart(e, comp.id, 's')"
            />
            <div
              class="absolute top-1/2 -left-1.5 -translate-y-1/2 w-3 h-3 bg-[#00d9ff] cursor-w-resize rounded-sm z-50"
              @mousedown="(e) => handleResizeStart(e, comp.id, 'w')"
            />
            <div
              class="absolute top-1/2 -right-1.5 -translate-y-1/2 w-3 h-3 bg-[#00d9ff] cursor-e-resize rounded-sm z-50"
              @mousedown="(e) => handleResizeStart(e, comp.id, 'e')"
            />
          </template>
        </div>
      </div>
    </div>
  </div>
</template>
