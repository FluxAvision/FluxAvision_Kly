<script setup lang="ts">
/**
 * 画布工作区 - 中间画布区域
 *
 * 交互功能：
 * - 从左侧面板拖拽组件到画布（drop / dragover）
 * - 单击选中组件，#00d9ff 高亮边框发光
 * - 拖拽移动选中组件（网格吸附）
 * - 右键上下文菜单（删除/复制）
 * - 8个缩放手柄（resize handles）
 * - 放置位置指示线
 * - 画布空白处点击取消选中
 * - 锁定组件不可选中不可拖拽
 */
import { ref, computed, type Component, defineAsyncComponent } from 'vue'
import type { TemplateConfig, ComponentConfig, ComponentType, ComponentStyles } from '@/types/template-editor'
import { useThemeResolver, resolveThemeCSSVars } from '@/components/large-screen/composables/useThemeResolver'
import { useLargeScreenData } from '@/components/large-screen/composables/useLargeScreenData'
import { getBorderBox, getDecoration } from '@/components/large-screen/datav-registry'

// ═══ Props & Emits ═══════════════════════════════════════════════════════

const props = defineProps<{
  templateConfig: TemplateConfig
  zoom: number
}>()

const emit = defineEmits<{
  selectComponent: [id: string | null]
  addComponent: [type: ComponentType, x: number, y: number]
  removeComponent: [id: string]
  duplicateComponent: [id: string]
  bringToFront: [id: string]
  updateComponentPosition: [id: string, x: number, y: number]
  confirmComponentPosition: [id: string, x: number, y: number]
  updateComponentSize: [id: string, width: number, height: number, x?: number, y?: number]
  confirmComponentSize: [id: string, width: number, height: number, x?: number, y?: number]
}>()

// ═══ 组件渲染映射 ═══════════════════════════════════════════════════════

const componentMap: Record<string, Component> = {
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
  'logo': defineAsyncComponent(() => import('@/components/template-editor/widgets/LogoImage.vue')),
  'line': defineAsyncComponent(() => import('@/components/template-editor/widgets/LineShape.vue')),
  'ranking-counter': defineAsyncComponent(() => import('@/components/template-editor/widgets/RankingCounter.vue')),
}

// ═══ 画布计算属性 ═══════════════════════════════════════════════════════

const canvasWidth = computed(() => props.templateConfig.canvas.width)
const canvasHeight = computed(() => props.templateConfig.canvas.height)
const hasComponents = computed(() => props.templateConfig.components.length > 0)

// 缩放后画布显示尺寸
const scaledWidth = computed(() => Math.round(canvasWidth.value * props.zoom / 100))
const scaledHeight = computed(() => Math.round(canvasHeight.value * props.zoom / 100))

// 组件列表（按 zIndex 排序）
const sortedComponents = computed(() => {
  return [...props.templateConfig.components]
    .filter(c => c.visible)
    .sort((a, b) => a.zIndex - b.zIndex)
})

// 网格配置
const gridSize = computed(() => props.templateConfig.canvas.grid?.size ?? 20)
const snapEnabled = computed(() => props.templateConfig.canvas.grid?.snapToGrid ?? true)

// 背景样式
const canvasBgStyle = computed(() => {
  const bg = props.templateConfig.canvas.background
  const style: Record<string, any> = {}

  if (bg) {
    switch (bg.type) {
      case 'color':
        style.backgroundColor = bg.color
        break
      case 'image':
        if (bg.image) {
          style.backgroundImage = `url(${bg.image})`
          style.backgroundSize = 'cover'
          style.backgroundPosition = 'center'
        }
        break
      case 'gradient':
        if (bg.gradient) style.background = bg.gradient
        break
      case 'decoration':
        style.backgroundColor = 'transparent'
        break
    }
    if (bg.opacity !== undefined) style.opacity = bg.opacity
  } else {
    style.backgroundColor = props.templateConfig.canvas.backgroundColor || '#0a192f'
  }

  return style
})

const hasDecorationBg = computed(() => {
  const bg = props.templateConfig.canvas.background
  return bg?.type === 'decoration' && !!bg.decorationType
})

// ═══ 数据映射 ═════════════════════════════════════════════════════════

const data = useLargeScreenData()

const componentDataMap = computed(() => {
  const map: Record<string, any> = {}
  for (const comp of props.templateConfig.components) {
    if (!comp.dataSource) {
      if (comp.type === 'metric-card' || comp.type === 'counter' || comp.type === 'ranking-counter') {
        map[comp.id] = { value: data.metrics.value['todayIn'] || 0, label: data.getLabel('todayIn') }
      } else if (comp.type === 'chart-line' || comp.type === 'chart-bar') {
        map[comp.id] = { hourlyData: data.hourlyData.value }
      } else {
        map[comp.id] = {}
      }
      continue
    }
    const { type, key } = comp.dataSource
    switch (type) {
      case 'metric':
        map[comp.id] = { value: data.metrics.value[key || ''] || 0, label: data.getLabel(key || '') }
        break
      case 'device':
        map[comp.id] = { device: data.allDevices.value.find(d => d.id === key) }
        break
      case 'hourly':
        map[comp.id] = { hourlyData: data.hourlyData.value }
        break
      default:
        if ((comp.type === 'metric-card' || comp.type === 'counter' || comp.type === 'ranking-counter') && key) {
          map[comp.id] = { value: data.metrics.value[key] || 0, label: data.getLabel(key) }
        } else if (comp.type === 'chart-line' || comp.type === 'chart-bar') {
          map[comp.id] = { hourlyData: data.hourlyData.value }
        } else {
          map[comp.id] = {}
        }
    }
  }
  return map
})

function getComponentData(comp: ComponentConfig) {
  return componentDataMap.value[comp.id] || {}
}

// ═══ 主题解析 ═════════════════════════════════════════════════════════

const theme = computed(() => props.templateConfig.canvas.theme)
const themeStyles = useThemeResolver(theme, sortedComponents.value)

function getComponentStyle(comp: ComponentConfig): Record<string, any> {
  const resolvedStyles = themeStyles.value.get(comp.id) as ComponentStyles | undefined

  const style: Record<string, any> = {
    position: 'absolute',
    left: `${comp.x}px`,
    top: `${comp.y}px`,
    width: `${comp.width}px`,
    height: `${comp.height}px`,
    zIndex: comp.zIndex,
    transform: `rotate(${comp.rotation}deg)`,
  }

  if (resolvedStyles) {
    const s = resolvedStyles as ComponentStyles
    style.opacity = s.opacity ?? comp.opacity
    if (s.backgroundGradient) {
      style.background = s.backgroundGradient
      if (s.backgroundColor) style.backgroundColor = s.backgroundColor
    } else if (s.backgroundColor) {
      style.backgroundColor = s.backgroundColor
    }
    if (s.backgroundImage) {
      style.backgroundImage = `url(${s.backgroundImage})`
      style.backgroundSize = s.backgroundSize || 'cover'
      style.backgroundPosition = 'center'
    }
    if (s.borderColor) style.borderColor = s.borderColor
    if (s.borderWidth) style.borderWidth = `${s.borderWidth}px`
    if (s.borderRadius) style.borderRadius = `${s.borderRadius}px`
    if (s.borderStyle) style.borderStyle = s.borderStyle
    if (s.color) style.color = s.color
    if (s.fontSize) style.fontSize = `${s.fontSize}px`
    if (s.fontWeight) style.fontWeight = s.fontWeight
    if (s.fontFamily) style.fontFamily = s.fontFamily
    if (s.textAlign) style.textAlign = s.textAlign
    if (s.lineHeight) style.lineHeight = s.lineHeight
    if (s.letterSpacing) style.letterSpacing = `${s.letterSpacing}px`
    if (s.textShadow) style.textShadow = s.textShadow
    if (s.padding) style.padding = `${s.padding}px`
    if (s.boxShadow) style.boxShadow = s.boxShadow
  } else {
    // Fallback to raw styles
    if (comp.styles) {
      const s = comp.styles
      style.opacity = s.opacity ?? comp.opacity
      if (s.backgroundColor) style.backgroundColor = s.backgroundColor
      if (s.color) style.color = s.color
      if (s.fontSize) style.fontSize = `${s.fontSize}px`
      if (s.borderRadius) style.borderRadius = `${s.borderRadius}px`
      if (s.boxShadow) style.boxShadow = s.boxShadow
    }
    if (!comp.styles && theme.value) {
      style.color = theme.value.textColor
      style.fontFamily = theme.value.fontFamily
    }
  }

  return style
}

function getAnimationStyle(comp: ComponentConfig): Record<string, any> {
  if (!comp.animation || comp.animation.type === 'none') return {}
  const anim = comp.animation
  const style: Record<string, any> = {
    animation: `${anim.type} ${anim.duration ?? 500}ms ${anim.easing ?? 'ease'} ${anim.delay ?? 0}ms`,
  }
  if (anim.repeat === 'infinite') style.animationIterationCount = 'infinite'
  else if (typeof anim.repeat === 'number') style.animationIterationCount = anim.repeat
  return style
}

// ═══ 选中状态 ═════════════════════════════════════════════════════════

const selectedId = ref<string | null>(null)

// 选中组件
function handleSelectComponent(id: string | null) {
  // 锁定组件不可选中
  if (id) {
    const comp = props.templateConfig.components.find(c => c.id === id)
    if (comp?.locked) return
  }
  selectedId.value = id
  emit('selectComponent', id)
}

// ═══ 拖拽放置（Drop）══════════════════════════════════════════════════

const isDragOver = ref(false)
const dropIndicator = ref<{ x: number; y: number } | null>(null)

// 拖拽经过画布
function handleDragOver(event: DragEvent) {
  event.preventDefault()
  if (!event.dataTransfer) return

  const dt = event.dataTransfer
  // 只接受我们的组件类型数据
  if (!dt.types.includes('application/x-component-type') && !dt.types.includes('text/plain')) return

  dt.dropEffect = 'copy'
  isDragOver.value = true

  // 计算放置指示位置
  const pos = getCanvasPosition(event)
  if (pos) {
    dropIndicator.value = pos
  }
}

function handleDragLeave() {
  isDragOver.value = false
  dropIndicator.value = null
}

// 放置组件
async function handleDrop(event: DragEvent) {
  event.preventDefault()
  isDragOver.value = false
  dropIndicator.value = null

  if (!event.dataTransfer) return

  const typeStr = event.dataTransfer.getData('application/x-component-type')
  if (!typeStr) return

  const compType = typeStr as ComponentType

  // 计算放置坐标
  const pos = getCanvasPosition(event)
  if (!pos) return

  // 网格吸附
  let x = pos.x
  let y = pos.y
  if (snapEnabled.value) {
    const gs = gridSize.value
    if (gs > 0) {
      x = Math.round(x / gs) * gs
      y = Math.round(y / gs) * gs
    }
  }

  // 居中放置（组件默认尺寸的一半偏移）
  const def = await getComponentDefaults(compType)
  x = Math.max(0, x - Math.round(def.width / 2))
  y = Math.max(0, y - Math.round(def.height / 2))

  emit('addComponent', compType, x, y)
}

// ═══ 组件拖拽移动 ═══════════════════════════════════════════════════

const isMoving = ref(false)
const moveStart = ref({ mouseX: 0, mouseY: 0, compX: 0, compY: 0 })
const movingId = ref<string | null>(null)

function handleComponentMouseDown(event: MouseEvent, comp: ComponentConfig) {
  if (event.button !== 0) return // 只响应左键
  // 如果没选中，先选中
  if (selectedId.value !== comp.id) {
    handleSelectComponent(comp.id)
  }

  // 锁定组件不可移动
  if (comp.locked) return

  event.stopPropagation()
  event.preventDefault()

  isMoving.value = true
  movingId.value = comp.id
  moveStart.value = {
    mouseX: event.clientX,
    mouseY: event.clientY,
    compX: comp.x,
    compY: comp.y,
  }

  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}

function handleMouseMove(event: MouseEvent) {
  if (!isMoving.value || !movingId.value) return

  const canvasEl = canvasRef.value
  if (!canvasEl) return

  const rect = canvasEl.getBoundingClientRect()
  const scale = props.zoom / 100

  // 计算鼠标在画布设计坐标中的偏移
  const dx = (event.clientX - moveStart.value.mouseX) / scale
  const dy = (event.clientY - moveStart.value.mouseY) / scale

  let newX = moveStart.value.compX + dx
  let newY = moveStart.value.compY + dy

  // 网格吸附
  if (snapEnabled.value) {
    const gs = gridSize.value
    if (gs > 0) {
      newX = Math.round(newX / gs) * gs
      newY = Math.round(newY / gs) * gs
    }
  }

  // 边界限制
  newX = Math.max(0, newX)
  newY = Math.max(0, newY)

  emit('updateComponentPosition', movingId.value, newX, newY)
}

function handleMouseUp() {
  if (isMoving.value && movingId.value) {
    const comp = props.templateConfig.components.find(c => c.id === movingId.value)
    if (comp) {
      emit('confirmComponentPosition', movingId.value, comp.x, comp.y)
    }
  }

  isMoving.value = false
  movingId.value = null
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
}

// ═══ 右键菜单 ══════════════════════════════════════════════════════

const contextMenu = ref<{
  visible: boolean
  x: number
  y: number
  compId: string
}>({
  visible: false,
  x: 0,
  y: 0,
  compId: '',
})

function handleContextMenu(event: MouseEvent, compId: string) {
  event.preventDefault()
  event.stopPropagation()

  // 先选中
  handleSelectComponent(compId)

  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    compId,
  }
}

function closeContextMenu() {
  contextMenu.value.visible = false
}

function handleContextDelete() {
  if (contextMenu.value.compId) {
    emit('removeComponent', contextMenu.value.compId)
  }
  closeContextMenu()
  handleSelectComponent(null)
}

function handleContextCopy() {
  if (contextMenu.value.compId) {
    emit('duplicateComponent', contextMenu.value.compId)
  }
  closeContextMenu()
}

// 点击画布空白处关闭右键菜单和取消选中
function handleCanvasClick(event: MouseEvent) {
  const target = event.target as HTMLElement
  // 如果点击的是组件包裹器或其子元素，不取消选中（组件自己已有 @click.stop）
  if (!target.closest('.designer-component-wrapper')) {
    handleSelectComponent(null)
  }
  closeContextMenu()
}

// ═══ 放置指示线位置 ═══════════════════════════════════════════════

function getCanvasPosition(event: DragEvent): { x: number; y: number } | null {
  const canvasEl = canvasRef.value
  if (!canvasEl) return null

  const rect = canvasEl.getBoundingClientRect()
  const scale = props.zoom / 100

  const relX = event.clientX - rect.left
  const relY = event.clientY - rect.top

  return {
    x: Math.round(relX / scale),
    y: Math.round(relY / scale),
  }
}

// ═══ 画布缩放 ref ═════════════════════════════════════════════════════

const canvasRef = ref<HTMLElement | null>(null)

// ═══ 缩放手柄 ═════════════════════════════════════════════════════

/** 缩放手柄类型 */
type ResizeHandle = 'tl' | 'tc' | 'tr' | 'rc' | 'br' | 'bc' | 'bl' | 'lc'

/** 缩放手柄状态 */
interface ResizeState {
  handle: ResizeHandle
  initMouseX: number
  initMouseY: number
  initComp: { x: number; y: number; width: number; height: number }
  compId: string
}

const isResizing = ref(false)
const resizeState = ref<ResizeState | null>(null)

const MIN_COMPONENT_SIZE = 20

function getHandleCursor(handle: ResizeHandle): string {
  const cursors: Record<ResizeHandle, string> = {
    'tl': 'nwse-resize',
    'tc': 'ns-resize',
    'tr': 'nesw-resize',
    'rc': 'ew-resize',
    'br': 'nwse-resize',
    'bc': 'ns-resize',
    'bl': 'nesw-resize',
    'lc': 'ew-resize',
  }
  return cursors[handle]
}

function handleResizeStart(event: MouseEvent, handle: ResizeHandle, comp: ComponentConfig) {
  if (event.button !== 0) return
  event.stopPropagation()
  event.preventDefault()

  isResizing.value = true
  resizeState.value = {
    handle,
    initMouseX: event.clientX,
    initMouseY: event.clientY,
    initComp: { x: comp.x, y: comp.y, width: comp.width, height: comp.height },
    compId: comp.id,
  }

  document.addEventListener('mousemove', handleResizeMove)
  document.addEventListener('mouseup', handleResizeEnd)
}

function handleResizeMove(event: MouseEvent) {
  if (!isResizing.value || !resizeState.value) return

  const canvasEl = canvasRef.value
  if (!canvasEl) return

  const rect = canvasEl.getBoundingClientRect()
  const scale = props.zoom / 100

  const dx = (event.clientX - resizeState.value.initMouseX) / scale
  const dy = (event.clientY - resizeState.value.initMouseY) / scale

  const { handle, initComp } = resizeState.value
  let newX = initComp.x
  let newY = initComp.y
  let newW = initComp.width
  let newH = initComp.height

  switch (handle) {
    case 'tl': // 左上角 → 同时调整 x,y,width,height（右下角固定）
      newX = initComp.x + dx
      newY = initComp.y + dy
      newW = initComp.width - dx
      newH = initComp.height - dy
      if (newW < MIN_COMPONENT_SIZE) {
        newW = MIN_COMPONENT_SIZE
        newX = initComp.x + initComp.width - MIN_COMPONENT_SIZE
      }
      if (newH < MIN_COMPONENT_SIZE) {
        newH = MIN_COMPONENT_SIZE
        newY = initComp.y + initComp.height - MIN_COMPONENT_SIZE
      }
      break
    case 'tc': // 上边 → 调整 y,height（下边固定）
      newY = initComp.y + dy
      newH = initComp.height - dy
      if (newH < MIN_COMPONENT_SIZE) {
        newH = MIN_COMPONENT_SIZE
        newY = initComp.y + initComp.height - MIN_COMPONENT_SIZE
      }
      break
    case 'tr': // 右上角 → 调整 y,width,height（左下角固定）
      newY = initComp.y + dy
      newW = initComp.width + dx
      newH = initComp.height - dy
      if (newW < MIN_COMPONENT_SIZE) {
        newW = MIN_COMPONENT_SIZE
      }
      if (newH < MIN_COMPONENT_SIZE) {
        newH = MIN_COMPONENT_SIZE
        newY = initComp.y + initComp.height - MIN_COMPONENT_SIZE
      }
      break
    case 'rc': // 右边 → 调整 width（左边固定）
      newW = initComp.width + dx
      if (newW < MIN_COMPONENT_SIZE) newW = MIN_COMPONENT_SIZE
      break
    case 'br': // 右下角 → 调整 width,height（左上角固定）
      newW = initComp.width + dx
      newH = initComp.height + dy
      if (newW < MIN_COMPONENT_SIZE) newW = MIN_COMPONENT_SIZE
      if (newH < MIN_COMPONENT_SIZE) newH = MIN_COMPONENT_SIZE
      break
    case 'bc': // 下边 → 调整 height（上边固定）
      newH = initComp.height + dy
      if (newH < MIN_COMPONENT_SIZE) newH = MIN_COMPONENT_SIZE
      break
    case 'bl': // 左下角 → 调整 x,width,height（右上角固定）
      newX = initComp.x + dx
      newW = initComp.width - dx
      newH = initComp.height + dy
      if (newW < MIN_COMPONENT_SIZE) {
        newW = MIN_COMPONENT_SIZE
        newX = initComp.x + initComp.width - MIN_COMPONENT_SIZE
      }
      if (newH < MIN_COMPONENT_SIZE) newH = MIN_COMPONENT_SIZE
      break
    case 'lc': // 左边 → 调整 x,width（右边固定）
      newX = initComp.x + dx
      newW = initComp.width - dx
      if (newW < MIN_COMPONENT_SIZE) {
        newW = MIN_COMPONENT_SIZE
        newX = initComp.x + initComp.width - MIN_COMPONENT_SIZE
      }
      break
  }

  // 网格吸附
  if (snapEnabled.value) {
    const gs = gridSize.value
    if (gs > 0) {
      newX = Math.round(newX / gs) * gs
      newY = Math.round(newY / gs) * gs
      newW = Math.round(newW / gs) * gs
      newH = Math.round(newH / gs) * gs
    }
  }

  // 边界约束
  newX = Math.max(0, newX)
  newY = Math.max(0, newY)
  newW = Math.max(MIN_COMPONENT_SIZE, newW)
  newH = Math.max(MIN_COMPONENT_SIZE, newH)

  emit('updateComponentSize', resizeState.value.compId, newW, newH, newX, newY)
}

function handleResizeEnd() {
  if (isResizing.value && resizeState.value) {
    const comp = props.templateConfig.components.find(c => c.id === resizeState.value!.compId)
    if (comp) {
      emit('confirmComponentSize', resizeState.value.compId, comp.width, comp.height, comp.x, comp.y)
    }
  }

  isResizing.value = false
  resizeState.value = null
  document.removeEventListener('mousemove', handleResizeMove)
  document.removeEventListener('mouseup', handleResizeEnd)
}

// ═══ 组件默认尺寸（用于居中放置）══════════════════════════════════

function getComponentDefaults(type: ComponentType): Promise<{ width: number; height: number }> {
  // 导入 COMPONENT_DEFINITIONS 来获取默认尺寸
  return import('@/types/template-editor').then(mod => {
    const def = mod.COMPONENT_DEFINITIONS.find(d => d.type === type)
    return def
      ? { width: def.defaultSize.width, height: def.defaultSize.height }
      : { width: 200, height: 100 }
  })
}


</script>

<template>
  <div class="canvas-workspace flex-1 flex flex-col bg-[#0d1b2a] overflow-hidden" @contextmenu.prevent>
    <!-- 画布顶部工具栏 -->
    <div class="h-8 flex items-center px-3 bg-[#0a192f] border-b border-[#1e293b]">
      <span class="text-xs text-[#8892a0]">
        设计尺寸: {{ canvasWidth }} x {{ canvasHeight }}
      </span>
      <span class="text-[#1e293b] mx-2">|</span>
      <span class="text-xs text-[#8892a0]">
        缩放: {{ zoom }}%
      </span>
      <span class="text-[#1e293b] mx-2">|</span>
      <span class="text-xs text-[#8892a0]">
        组件: {{ props.templateConfig.components.length }}
      </span>
    </div>

    <!-- 画布容器 -->
    <div class="flex-1 flex items-start justify-center overflow-auto p-8">
      <!-- 空状态 -->
      <div
        v-if="!hasComponents"
        class="canvas-empty-state flex flex-col items-center justify-center h-full text-center"
        @click="handleCanvasClick"
      >
        <div class="w-16 h-16 mb-4 rounded-2xl bg-[#112240] flex items-center justify-center border-2 border-dashed border-[#1e293b]">
          <svg class="w-8 h-8 text-[#1e293b]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <path d="M9 12h6" />
            <path d="M12 9v6" />
          </svg>
        </div>
        <p class="text-[#8892a0] text-sm">从左侧拖拽组件到画布</p>
        <p class="text-[#5a6a80] text-xs mt-1">或点击组件面板中的组件添加</p>
      </div>

      <!-- 画布 -->
      <div
        v-else
        ref="canvasRef"
        class="relative shadow-2xl canvas-drop-zone"
        :class="{
          'drag-over': isDragOver,
          'cursor-grab': selectedId !== null,
        }"
        :style="{
          width: scaledWidth + 'px',
          height: scaledHeight + 'px',
          minWidth: scaledWidth + 'px',
          minHeight: scaledHeight + 'px',
        }"
        @dragover="handleDragOver"
        @dragleave="handleDragLeave"
        @drop="handleDrop"
        @click="handleCanvasClick"
      >
        <!-- 尺寸标注角标 -->
        <div class="absolute -top-6 left-0 text-xs text-[#8892a0] select-none">
          {{ canvasWidth }}px
        </div>
        <div class="absolute -left-14 top-1/2 -translate-y-1/2 text-xs text-[#8892a0] select-none -rotate-90 origin-center whitespace-nowrap">
          {{ canvasHeight }}px
        </div>

        <!-- 尺寸标注线（顶部） -->
        <div class="absolute -top-[1px] left-0 right-0 h-px bg-[#00d9ff]/30" />
        <div class="absolute -left-[1px] top-0 bottom-0 w-px bg-[#00d9ff]/30" />

        <!-- 缩放容器 -->
        <div
          :style="{
            transform: `scale(${zoom / 100})`,
            transformOrigin: '0 0',
            width: canvasWidth + 'px',
            height: canvasHeight + 'px',
            overflow: 'hidden',
          }"
          class="relative"
        >
          <!-- 画布背景 -->
          <div
            class="absolute inset-0"
            :style="canvasBgStyle"
          >
            <!-- Decoration 类型背景 -->
            <div
              v-if="hasDecorationBg"
              class="absolute inset-0 pointer-events-none"
              :style="{ opacity: templateConfig.canvas.background?.opacity ?? 1 }"
            >
              <component
                :is="getDecoration(templateConfig.canvas.background?.decorationType)"
                class="w-full h-full"
              />
            </div>

            <!-- 背景蒙层 -->
            <div
              v-if="templateConfig.canvas.background?.overlay"
              class="absolute inset-0 pointer-events-none z-[1]"
              :style="{ backgroundColor: templateConfig.canvas.background.overlay }"
            />
          </div>

          <!-- 渲染组件 -->
          <template v-for="comp in sortedComponents" :key="comp.id">
            <div
              class="designer-component-wrapper"
              :class="{
                'is-selected': selectedId === comp.id,
                'is-moving': isMoving && movingId === comp.id,
                'is-locked': comp.locked,
              }"
              :style="[getComponentStyle(comp), getAnimationStyle(comp)]"
              @mousedown.stop="handleComponentMouseDown($event, comp)"
              @contextmenu.stop="!comp.locked && handleContextMenu($event, comp.id)"
              @click.stop="handleSelectComponent(comp.id)"
            >
              <!-- 选中高亮框 -->
              <div
                v-if="selectedId === comp.id"
                class="absolute -inset-[2px] rounded pointer-events-none selection-highlight"
              />

              <!-- 缩放手柄（选中且未锁定时显示 8 个拖拽方块） -->
              <template v-if="selectedId === comp.id && !comp.locked">
                <div class="resize-handle resize-handle-tl" @mousedown.stop="handleResizeStart($event, 'tl', comp)" />
                <div class="resize-handle resize-handle-tc" @mousedown.stop="handleResizeStart($event, 'tc', comp)" />
                <div class="resize-handle resize-handle-tr" @mousedown.stop="handleResizeStart($event, 'tr', comp)" />
                <div class="resize-handle resize-handle-rc" @mousedown.stop="handleResizeStart($event, 'rc', comp)" />
                <div class="resize-handle resize-handle-br" @mousedown.stop="handleResizeStart($event, 'br', comp)" />
                <div class="resize-handle resize-handle-bc" @mousedown.stop="handleResizeStart($event, 'bc', comp)" />
                <div class="resize-handle resize-handle-bl" @mousedown.stop="handleResizeStart($event, 'bl', comp)" />
                <div class="resize-handle resize-handle-lc" @mousedown.stop="handleResizeStart($event, 'lc', comp)" />
              </template>

              <!-- 组件内容 -->
              <!-- Decoration 类型直接渲染 -->
              <template v-if="comp.type === 'decoration'">
                <component
                  :is="componentMap[comp.type]"
                  :config="comp"
                  :data="getComponentData(comp)"
                  class="w-full h-full"
                />
              </template>

              <!-- 其他类型，可选 BorderBox 包装 -->
              <template v-else>
                <component
                  v-if="comp.border?.type && getBorderBox(comp.border.type)"
                  :is="getBorderBox(comp.border.type)!"
                  :color="comp.border.color"
                  :backgroundColor="comp.border.backgroundColor"
                  class="w-full h-full"
                >
                  <component
                    :is="componentMap[comp.type]"
                    :config="comp"
                    :data="getComponentData(comp)"
                    class="w-full h-full"
                  />
                </component>

                <component
                  v-else
                  :is="componentMap[comp.type]"
                  :config="comp"
                  :data="getComponentData(comp)"
                  class="w-full h-full"
                />
              </template>
            </div>
          </template>

          <!-- 放置指示线（鼠标经过画布时显示） -->
          <div
            v-if="isDragOver && dropIndicator"
            class="absolute pointer-events-none z-[9999]"
            :style="{
              left: (dropIndicator.x - 1) + 'px',
              top: (dropIndicator.y - 1) + 'px',
            }"
          >
            <!-- 十字交叉线 -->
            <div class="absolute w-3 h-px bg-[#00d9ff]/80 -translate-x-1/2 -translate-y-1/2" />
            <div class="absolute h-3 w-px bg-[#00d9ff]/80 -translate-x-1/2 -translate-y-1/2" />
          </div>
        </div>
      </div>
    </div>

    <!-- 右键上下文菜单 -->
    <Teleport to="body">
      <div
        v-if="contextMenu.visible"
        class="fixed inset-0 z-[10000]"
        @click="closeContextMenu"
        @contextmenu.prevent="closeContextMenu"
      />
      <div
        v-if="contextMenu.visible"
        class="fixed z-[10001] bg-[#112240] border border-[#1e293b] rounded-lg shadow-xl py-1 min-w-[120px]"
        :style="{
          left: contextMenu.x + 'px',
          top: contextMenu.y + 'px',
        }"
      >
        <button
          class="w-full flex items-center gap-2 px-3 py-2 text-xs text-[#ccd6f6] hover:bg-[#1e293b] transition-colors cursor-pointer"
          @click="handleContextCopy"
        >
          <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="9" y="9" width="13" height="13" rx="2" />
            <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
          </svg>
          复制
        </button>
        <div class="mx-2 border-t border-[#1e293b]" />
        <button
          class="w-full flex items-center gap-2 px-3 py-2 text-xs text-[#f43f5e] hover:bg-[#1e293b] transition-colors cursor-pointer"
          @click="handleContextDelete"
        >
          <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
          </svg>
          删除
        </button>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.canvas-workspace {
  background-image:
    radial-gradient(circle, #1e293b 0.5px, transparent 0.5px);
  background-size: 20px 20px;
}

.canvas-drop-zone {
  transition: box-shadow 0.2s;
}

.canvas-drop-zone.drag-over {
  box-shadow: 0 0 30px rgba(100, 255, 218, 0.15), inset 0 0 30px rgba(100, 255, 218, 0.05);
}

.cursor-grab {
  cursor: grab;
}

.cursor-grab:active {
  cursor: grabbing;
}

/* 组件包裹器 */
.designer-component-wrapper {
  position: absolute;
  cursor: pointer;
  transition: opacity 0.15s;
  user-select: none;
}

.designer-component-wrapper:hover {
  outline: 1px solid rgba(100, 255, 218, 0.3);
  outline-offset: -1px;
}

.designer-component-wrapper.is-selected {
  cursor: grab;
  z-index: 100 !important;
}

.designer-component-wrapper.is-moving {
  cursor: grabbing;
  opacity: 0.85;
}

/* 缩放手柄容器保证 z-index 高于组件 */
.designer-component-wrapper {
  contain: layout style;
}

/* 缩放手柄通用样式 */
.resize-handle {
  position: absolute;
  width: 8px;
  height: 8px;
  background: #ffffff;
  border: 1px solid #00d9ff;
  box-shadow: 0 1px 4px rgba(0, 217, 255, 0.3);
  z-index: 101;
  border-radius: 1px;
  transition: background 0.1s;
}

.resize-handle:hover {
  background: #00d9ff;
}

/* 定位 */
.resize-handle-tl { top: -4px; left: -4px; cursor: nwse-resize; }
.resize-handle-tc { top: -4px; left: calc(50% - 4px); cursor: ns-resize; }
.resize-handle-tr { top: -4px; right: -4px; cursor: nesw-resize; }
.resize-handle-rc { top: calc(50% - 4px); right: -4px; cursor: ew-resize; }
.resize-handle-br { bottom: -4px; right: -4px; cursor: nwse-resize; }
.resize-handle-bc { bottom: -4px; left: calc(50% - 4px); cursor: ns-resize; }
.resize-handle-bl { bottom: -4px; left: -4px; cursor: nesw-resize; }
.resize-handle-lc { top: calc(50% - 4px); left: -4px; cursor: ew-resize; }

.designer-component-wrapper.is-locked {
  cursor: not-allowed;
  opacity: 0.7;
}

.designer-component-wrapper.is-locked::after {
  content: '';
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    45deg,
    transparent,
    transparent 4px,
    rgba(244, 63, 94, 0.08) 4px,
    rgba(244, 63, 94, 0.08) 8px
  );
  pointer-events: none;
  z-index: 5;
}

.designer-component-wrapper.is-locked:hover {
  outline: 1px solid rgba(244, 63, 94, 0.3);
  outline-offset: -1px;
}

/* 选中高亮 */
.selection-highlight {
  border: 2px solid #00d9ff;
  box-shadow:
    0 0 8px rgba(100, 255, 218, 0.4),
    inset 0 0 8px rgba(100, 255, 218, 0.1);
  animation: selection-pulse 2s ease-in-out infinite;
}

@keyframes selection-pulse {
  0%, 100% {
    box-shadow:
      0 0 8px rgba(100, 255, 218, 0.4),
      inset 0 0 8px rgba(100, 255, 218, 0.1);
  }
  50% {
    box-shadow:
      0 0 12px rgba(100, 255, 218, 0.6),
      inset 0 0 12px rgba(100, 255, 218, 0.2);
  }
}

/* 滚动条 */
.canvas-workspace :deep()::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.canvas-workspace :deep()::-webkit-scrollbar-track {
  background: #0d1b2a;
}

.canvas-workspace :deep()::-webkit-scrollbar-thumb {
  background: #1e293b;
  border-radius: 3px;
}
</style>
