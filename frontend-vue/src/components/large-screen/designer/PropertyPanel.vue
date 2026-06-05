<script setup lang="ts">
/**
 * 右侧属性面板 - PropertyPanel.vue
 *
 * 5 个标签页：
 * 1. 样式（styles） - 位置/尺寸/旋转/透明度/对齐/边距/背景色/边框/阴影
 * 2. 数据（data） - 数据源绑定
 * 3. 属性（props） - 组件特有属性
 * 4. 动画（animation） - 入场/强调/退场动画
 * 5. 高级（advanced） - 模板编辑模式/全局画布配置
 *
 * 当 templateEditMode 为 true 时，展示画布全局配置
 */
import { ref, computed, watch, onMounted } from 'vue'
import type {
  ComponentConfig,
  TemplateConfig,
  ComponentStyles,
  DataSourceConfig,
  ComponentType,
} from '@/types/template-editor'
import { METRIC_OPTIONS } from '@/types/template-editor'

const props = defineProps<{
  selectedComponent: ComponentConfig | null
  templateConfig: TemplateConfig
  templateEditMode: boolean
  selectedComponentId: string | null
}>()

const emit = defineEmits<{
  'toggle-template-edit-mode': []
  'update-component': [id: string, updates: Partial<ComponentConfig>]
  'update-component-styles': [id: string, styles: Partial<ComponentStyles>]
  'update-component-props': [id: string, props: Record<string, any>]
  'update-data-source': [id: string, ds: Partial<DataSourceConfig> | undefined]
  'update-component-animation': [id: string, anim: Partial<any> | undefined]
  'update-canvas': [updates: Partial<Record<string, any>>]
  'update-canvas-background': [updates: Record<string, any>]
  'update-canvas-theme': [updates: Record<string, any>]
  'push-history': []
  'select-component': [id: string | null]
}>()

// ─── Tab 状态 ──────────────────────────────────

type PropertyTab = 'styles' | 'data' | 'props' | 'animation' | 'advanced'

const activeTab = ref<PropertyTab>('styles')

// 当选中组件变化时，重置到样式 Tab
watch(() => props.selectedComponentId, () => {
  activeTab.value = 'styles'
})

// ─── Tab 列表 ──────────────────────────────────

interface TabItem {
  key: PropertyTab
  label: string
  icon: string
}

const tabs: TabItem[] = [
  { key: 'styles', label: '样式', icon: 'M12 20V10M18 20V4M6 20v-4' },
  { key: 'data', label: '数据', icon: 'M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z M12 15a3 3 0 100-6 3 3 0 000 6z' },
  { key: 'props', label: '属性', icon: 'M16 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2 M8.5 7a4 4 0 100-8 4 4 0 000 8z M20 8l-3 3 3 3' },
  { key: 'animation', label: '动画', icon: 'M13 2L3 14h9l-1 8 10-12h-9l1-8z' },
  { key: 'advanced', label: '高级', icon: 'M12 15V3m0 12l-4-4m4 4l4-4M2 17l.621 2.485A2 2 0 004.561 21h14.878a2 2 0 001.94-1.515L22 17' },
]

// ─── 画布数据 ──────────────────────────────────

const canvas = computed(() => props.templateConfig.canvas)

// ─── 样式 Tab 数据 ────────────────────────────

const localStyles = ref<ComponentStyles>({})
const localPosition = ref({ x: 0, y: 0, width: 200, height: 100, rotation: 0, opacity: 1 })

// 同步选中组件数据到本地
watch(() => props.selectedComponent, (comp) => {
  if (comp) {
    localPosition.value = {
      x: comp.x,
      y: comp.y,
      width: comp.width,
      height: comp.height,
      rotation: comp.rotation,
      opacity: comp.opacity,
    }
    localStyles.value = { ...(comp.styles || {}) }
  }
}, { immediate: true, deep: true })

function applyPosition() {
  if (!props.selectedComponentId) return
  emit('update-component', props.selectedComponentId, localPosition.value)
  emit('push-history')
}

function applyStyles() {
  if (!props.selectedComponentId) return
  emit('update-component-styles', props.selectedComponentId, localStyles.value)
  emit('push-history')
}

// ─── 数据 Tab ──────────────────────────────────

const localDataSource = ref<DataSourceConfig | undefined>(undefined)

watch(() => props.selectedComponent, (comp) => {
  if (comp) {
    localDataSource.value = comp.dataSource ? { ...comp.dataSource } : undefined
  }
}, { immediate: true })

function applyDataSource(type: string | undefined) {
  if (!props.selectedComponentId) return
  if (!type) {
    emit('update-data-source', props.selectedComponentId, undefined)
  } else {
    emit('update-data-source', props.selectedComponentId, { type: type as any })
  }
  emit('push-history')
}

function applyDataSourceKey(key: string) {
  if (!props.selectedComponentId || !localDataSource.value) return
  emit('update-data-source', props.selectedComponentId, { key })
  emit('push-history')
}

// ─── 设备列表（用于视频组件数据绑定） ──────────

interface DeviceItem {
  id: string
  name: string
  status?: string
  ip?: string
  location?: string
}

const devices = ref<DeviceItem[]>([])
const devicesLoading = ref(false)

async function fetchDevices() {
  devicesLoading.value = true
  try {
    const res = await fetch('/api/devices')
    if (res.ok) {
      const json = await res.json()
      devices.value = json.data || json || []
    }
  } catch {
    devices.value = []
  } finally {
    devicesLoading.value = false
  }
}

const selectedDeviceName = computed(() => {
  const key = localDataSource.value?.key || props.selectedComponent?.dataSource?.key
  if (!key) return null
  const device = devices.value.find(d => d.id === key)
  return device?.name || null
})

// ─── 属性 Tab ──────────────────────────────────

const localProps = ref<Record<string, any>>({})

watch(() => props.selectedComponent, (comp) => {
  if (comp) {
    localProps.value = { ...(comp.props || {}) }
  }
}, { immediate: true, deep: true })

const logoFileInput = ref<HTMLInputElement | null>(null)
function triggerLogoUpload() { logoFileInput.value?.click() }
function handleLogoFileUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (e) => { localProps.value.logoSrc = e.target?.result as string; applyProps() }
  reader.readAsDataURL(file)
  input.value = ''
}

function applyProps() {
  if (!props.selectedComponentId) return
  emit('update-component-props', props.selectedComponentId, localProps.value)
  emit('push-history')
}

// 获取视频墙设备ID数组（从 cellDeviceIds）
function getVideoWallDeviceIds(): string[] {
  const ids = localProps.value.cellDeviceIds ? [...localProps.value.cellDeviceIds] : []
  const cols = localProps.value.gridCols ?? 2
  const rows = localProps.value.gridRows ?? 1
  const total = cols * rows
  while (ids.length < total) ids.push('')
  return ids.slice(0, total)
}

// 批量更新视频墙格子设备信息（id/name/ip/rtspUrl 四个数组同时更新）
function updateVideoWallCell(index: number, deviceId: string) {
  const device = devices.value.find(d => d.id === deviceId)

  // cellDeviceIds
  const ids = localProps.value.cellDeviceIds ? [...localProps.value.cellDeviceIds] : []
  while (ids.length <= index) ids.push('')
  ids[index] = deviceId
  localProps.value.cellDeviceIds = ids

  // cellDeviceNames
  const names = localProps.value.cellDeviceNames ? [...localProps.value.cellDeviceNames] : []
  while (names.length <= index) names.push('')
  names[index] = device?.name || ''
  localProps.value.cellDeviceNames = names

  // cellDeviceIps
  const ips = localProps.value.cellDeviceIps ? [...localProps.value.cellDeviceIps] : []
  while (ips.length <= index) ips.push('')
  ips[index] = device?.ip || ''
  localProps.value.cellDeviceIps = ips

  // cellRtspUrls
  const rtspUrls = localProps.value.cellRtspUrls ? [...localProps.value.cellRtspUrls] : []
  while (rtspUrls.length <= index) rtspUrls.push('')
  rtspUrls[index] = (device as any)?.rtspUrl || ''
  localProps.value.cellRtspUrls = rtspUrls

  applyProps()
}

// 同步视频墙所有数组到新的宫格数量
function syncVideoWallArrays(newCount: number) {
  const fields = ['cellDeviceIds', 'cellDeviceNames', 'cellDeviceIps', 'cellRtspUrls'] as const
  for (const field of fields) {
    const arr = localProps.value[field] ? [...localProps.value[field]] : []
    while (arr.length < newCount) arr.push('')
    while (arr.length > newCount) arr.pop()
    localProps.value[field] = arr
  }
  applyProps()
}

// ─── 动画 Tab ──────────────────────────────────

const localAnimation = ref<{ type: string; duration?: number; delay?: number; repeat?: number | string }>({ type: 'none' })

watch(() => props.selectedComponent, (comp) => {
  if (comp && comp.animation) {
    localAnimation.value = { ...comp.animation }
  } else {
    localAnimation.value = { type: 'none' }
  }
}, { immediate: true, deep: true })

const animationPresets = [
  { value: 'none', label: '无动画' },
  { value: 'fadeIn', label: '淡入' },
  { value: 'fadeInDown', label: '从上淡入' },
  { value: 'fadeInUp', label: '从下淡入' },
  { value: 'fadeInLeft', label: '从左淡入' },
  { value: 'fadeInRight', label: '从右淡入' },
  { value: 'zoomIn', label: '放大进入' },
  { value: 'bounceIn', label: '弹跳进入' },
  { value: 'slideInUp', label: '上滑进入' },
  { value: 'slideInDown', label: '下滑进入' },
  { value: 'rotateIn', label: '旋转进入' },
  { value: 'flipInX', label: '水平翻转' },
  { value: 'flipInY', label: '垂直翻转' },
  { value: 'pulse', label: '脉冲强调' },
  { value: 'shake', label: '抖动强调' },
  { value: 'flash', label: '闪烁强调' },
  { value: 'swing', label: '摇摆强调' },
  { value: 'heartBeat', label: '心跳强调' },
  { value: 'bounce', label: '弹跳强调' },
]

function applyAnimation() {
  if (!props.selectedComponentId) return
  const anim = localAnimation.value.type === 'none' ? undefined : { ...localAnimation.value }
  emit('update-component-animation', props.selectedComponentId, anim)
  emit('push-history')
}

// ─── 画布配置（高级 Tab / 模板编辑模式）──────

const localCanvasWidth = ref(1920)
const localCanvasHeight = ref(1080)
const localCanvasBg = ref('#0a192f')
const localGridSize = ref(20)
const localSnapEnabled = ref(true)

watch(() => props.templateConfig, (cfg) => {
  localCanvasWidth.value = cfg.canvas.width
  localCanvasHeight.value = cfg.canvas.height
  localCanvasBg.value = cfg.canvas.backgroundColor
  localGridSize.value = cfg.canvas.grid?.size ?? 20
  localSnapEnabled.value = cfg.canvas.grid?.snapToGrid ?? true
}, { immediate: true, deep: true })

function applyCanvasConfig() {
  emit('update-canvas', {
    width: localCanvasWidth.value,
    height: localCanvasHeight.value,
    backgroundColor: localCanvasBg.value,
    grid: {
      enabled: true,
      size: localGridSize.value,
      snapToGrid: localSnapEnabled.value,
    },
  })
  emit('push-history')
}

// ─── 通用编辑辅助 ─────────────────────────────

function handleColorInput(event: Event, setter: (val: string) => void) {
  const val = (event.target as HTMLInputElement).value
  setter(val)
}

onMounted(() => {
  fetchDevices()
})
</script>

<template>
  <div class="property-panel w-[300px] flex flex-col bg-[#0a192f] border-l border-[#1e293b] flex-shrink-0">
    <!-- 标题栏 -->
    <div class="h-12 flex items-center px-4 border-b border-[#1e293b]">
      <span class="text-sm font-semibold text-white">
        {{ templateEditMode ? '画布配置' : (selectedComponent ? selectedComponent.name : '属性') }}
      </span>
      <span v-if="selectedComponent && !templateEditMode" class="text-[10px] text-[#5a6a80] ml-2">
        {{ selectedComponent.type }}
      </span>
    </div>

    <!-- Tab 导航 -->
    <div class="flex border-b border-[#1e293b]">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="flex-1 h-9 flex items-center justify-center gap-1 text-xs transition-colors cursor-pointer"
        :class="activeTab === tab.key ? 'text-[#00d9ff] border-b-2 border-[#00d9ff]' : 'text-[#5a6a80] hover:text-white'"
        @click="activeTab = tab.key"
      >
        <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path :d="tab.icon" />
        </svg>
        {{ tab.label }}
      </button>
    </div>

    <!-- 模板编辑模式下的画布配置 -->
    <div v-if="templateEditMode" class="flex-1 overflow-y-auto p-4 space-y-4">
      <div class="space-y-3">
        <h4 class="text-xs font-medium text-[#8892a0] uppercase tracking-wider">画布尺寸</h4>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs text-[#5a6a80] mb-1">宽度 (px)</label>
            <input
              v-model.number="localCanvasWidth"
              type="number"
              class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors"
              min="800"
              max="7680"
              @change="applyCanvasConfig"
            />
          </div>
          <div>
            <label class="block text-xs text-[#5a6a80] mb-1">高度 (px)</label>
            <input
              v-model.number="localCanvasHeight"
              type="number"
              class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors"
              min="600"
              max="4320"
              @change="applyCanvasConfig"
            />
          </div>
        </div>
      </div>

      <div class="space-y-3">
        <h4 class="text-xs font-medium text-[#8892a0] uppercase tracking-wider">背景</h4>
        <div>
          <label class="block text-xs text-[#5a6a80] mb-1">背景颜色</label>
          <div class="flex items-center gap-0 rounded-md border border-[#1e293b] overflow-hidden">
            <input
              type="color"
              :value="localCanvasBg"
              @input="handleColorInput($event, v => { localCanvasBg = v; applyCanvasConfig() })"
              class="w-10 h-8 cursor-pointer border-0 p-0.5 bg-transparent"
              style="flex-shrink:0;min-width:40px;"
            />
            <input
              :value="localCanvasBg"
              @input="handleColorInput($event, v => { localCanvasBg = v; applyCanvasConfig() })"
              class="flex-1 h-8 px-2.5 text-xs text-white font-mono outline-none bg-[#112240]"
              style="border:none!important;"
            />
          </div>
        </div>
      </div>

      <div class="space-y-3">
        <h4 class="text-xs font-medium text-[#8892a0] uppercase tracking-wider">网格</h4>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs text-[#5a6a80] mb-1">网格大小 (px)</label>
            <input
              v-model.number="localGridSize"
              type="number"
              class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors"
              min="5"
              max="100"
              @change="applyCanvasConfig"
            />
          </div>
          <div class="flex items-end pb-1">
            <label class="flex items-center gap-2 cursor-pointer">
              <input
                v-model="localSnapEnabled"
                type="checkbox"
                class="w-4 h-4 rounded border-[#2d4765] accent-[#00d9ff]"
                @change="applyCanvasConfig"
              />
              <span class="text-xs text-[#8892a0]">吸附网格</span>
            </label>
          </div>
        </div>
      </div>

      <div class="pt-2">
        <button
          class="w-full h-8 rounded-md bg-[#00d9ff] text-[#0a192f] text-xs font-semibold hover:bg-[#00d9ff]/80 cursor-pointer transition-colors"
          @click="emit('toggle-template-edit-mode')"
        >
          退出画布配置
        </button>
      </div>
    </div>

    <!-- 未选中组件 && 非模板编辑模式 -->
    <div
      v-else-if="!selectedComponent"
      class="flex-1 flex flex-col items-center justify-center text-center p-6"
    >
      <svg class="w-12 h-12 text-[#1e293b] mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <line x1="9" y1="9" x2="15" y2="15" />
        <line x1="15" y1="9" x2="9" y2="15" />
      </svg>
      <p class="text-sm text-[#8892a0]">未选中组件</p>
      <p class="text-xs text-[#5a6a80] mt-1">点击画布上的组件以编辑属性</p>
    </div>

    <!-- 选中组件 → 属性编辑 -->
    <div
      v-else
      class="flex-1 overflow-y-auto"
    >
      <!-- ═══════════════ 样式 Tab ═══════════════ -->
      <div v-if="activeTab === 'styles'" class="p-4 space-y-4">
        <!-- 位置与尺寸 -->
        <div class="space-y-3">
          <h4 class="text-xs font-medium text-[#8892a0] uppercase tracking-wider">位置与尺寸</h4>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">X</label>
              <input
                v-model.number="localPosition.x"
                type="number"
                class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors"
                @change="applyPosition"
              />
            </div>
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">Y</label>
              <input
                v-model.number="localPosition.y"
                type="number"
                class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors"
                @change="applyPosition"
              />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">宽度</label>
              <input
                v-model.number="localPosition.width"
                type="number"
                class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors"
                min="20"
                @change="applyPosition"
              />
            </div>
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">高度</label>
              <input
                v-model.number="localPosition.height"
                type="number"
                class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors"
                min="20"
                @change="applyPosition"
              />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">旋转 (°)</label>
              <input
                v-model.number="localPosition.rotation"
                type="number"
                class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors"
                @change="applyPosition"
              />
            </div>
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">透明度</label>
              <div class="flex items-center gap-2">
                <input
                  v-model.number="localPosition.opacity"
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  class="flex-1 accent-[#00d9ff]"
                  @change="applyPosition"
                />
                <span class="text-xs text-white font-mono w-8 text-right">
                  {{ Math.round(localPosition.opacity * 100) }}%
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="border-t border-[#1e293b]" />

        <!-- 排版 -->
        <div class="space-y-3">
          <h4 class="text-xs font-medium text-[#8892a0] uppercase tracking-wider">排版</h4>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">字体大小</label>
              <input
                v-model.number="localStyles.fontSize"
                type="number"
                class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors"
                min="10"
                max="200"
                @change="applyStyles"
              />
            </div>
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">字体粗细</label>
              <select
                v-model="localStyles.fontWeight"
                class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors appearance-none cursor-pointer"
                @change="applyStyles"
              >
                <option value="normal">正常</option>
                <option value="bold">粗体</option>
                <option value="100">100</option>
                <option value="200">200</option>
                <option value="300">300</option>
                <option value="400">400</option>
                <option value="500">500</option>
                <option value="600">600</option>
                <option value="700">700</option>
                <option value="800">800</option>
                <option value="900">900</option>
              </select>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">颜色</label>
              <div class="flex items-center gap-0 rounded-md border border-[#1e293b] overflow-hidden">
                <input
                  type="color"
                  :value="localStyles.color || '#ffffff'"
                  @input="handleColorInput($event, v => { localStyles.color = v; applyStyles() })"
                  class="w-10 h-8 cursor-pointer border-0 p-0.5 bg-transparent"
                  style="flex-shrink:0;min-width:40px;"
                />
                <input
                  :value="localStyles.color || ''"
                  @input="handleColorInput($event, v => { localStyles.color = v; applyStyles() })"
                  class="flex-1 h-8 px-2.5 text-xs text-white font-mono outline-none bg-[#112240]"
                  style="border:none!important;"
                  placeholder="#ffffff"
                />
              </div>
            </div>
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">对齐</label>
              <div class="flex h-8 gap-1">
                <button
                  class="flex-1 flex items-center justify-center rounded-md border cursor-pointer transition-colors"
                  :class="localStyles.textAlign === 'left' ? 'border-[#00d9ff] bg-[#00d9ff]/10 text-[#00d9ff]' : 'border-[#1e293b] bg-[#112240] text-[#8892a0] hover:border-[#00d9ff]/30'"
                  @click="localStyles.textAlign = 'left'; applyStyles()"
                >
                  <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="17" y1="10" x2="3" y2="10"/><line x1="21" y1="6" x2="3" y2="6"/><line x1="17" y1="14" x2="3" y2="14"/><line x1="21" y1="18" x2="3" y2="18"/></svg>
                </button>
                <button
                  class="flex-1 flex items-center justify-center rounded-md border cursor-pointer transition-colors"
                  :class="localStyles.textAlign === 'center' ? 'border-[#00d9ff] bg-[#00d9ff]/10 text-[#00d9ff]' : 'border-[#1e293b] bg-[#112240] text-[#8892a0] hover:border-[#00d9ff]/30'"
                  @click="localStyles.textAlign = 'center'; applyStyles()"
                >
                  <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="10" x2="6" y2="10"/><line x1="21" y1="6" x2="3" y2="6"/><line x1="18" y1="14" x2="6" y2="14"/><line x1="21" y1="18" x2="3" y2="18"/></svg>
                </button>
                <button
                  class="flex-1 flex items-center justify-center rounded-md border cursor-pointer transition-colors"
                  :class="localStyles.textAlign === 'right' ? 'border-[#00d9ff] bg-[#00d9ff]/10 text-[#00d9ff]' : 'border-[#1e293b] bg-[#112240] text-[#8892a0] hover:border-[#00d9ff]/30'"
                  @click="localStyles.textAlign = 'right'; applyStyles()"
                >
                  <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="21" y1="10" x2="7" y2="10"/><line x1="21" y1="6" x2="3" y2="6"/><line x1="21" y1="14" x2="7" y2="14"/><line x1="21" y1="18" x2="3" y2="18"/></svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="border-t border-[#1e293b]" />

        <!-- 边框与圆角 -->
        <div class="space-y-3">
          <h4 class="text-xs font-medium text-[#8892a0] uppercase tracking-wider">边框与圆角</h4>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">背景色</label>
              <div class="flex items-center gap-0 rounded-md border border-[#1e293b] overflow-hidden">
                <input
                  type="color"
                  :value="localStyles.backgroundColor || 'transparent'"
                  @input="handleColorInput($event, v => { localStyles.backgroundColor = v; applyStyles() })"
                  class="w-10 h-8 cursor-pointer border-0 p-0.5 bg-transparent"
                  style="flex-shrink:0;min-width:40px;"
                />
                <input
                  :value="localStyles.backgroundColor || ''"
                  @input="handleColorInput($event, v => { localStyles.backgroundColor = v || undefined; applyStyles() })"
                  class="flex-1 h-8 px-2.5 text-xs text-white font-mono outline-none bg-[#112240]"
                  style="border:none!important;"
                  placeholder="transparent"
                />
              </div>
            </div>
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">圆角</label>
              <input
                v-model.number="localStyles.borderRadius"
                type="number"
                class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors"
                min="0"
                max="100"
                @change="applyStyles"
              />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">边框颜色</label>
              <div class="flex items-center gap-0 rounded-md border border-[#1e293b] overflow-hidden">
                <input
                  type="color"
                  :value="localStyles.borderColor || 'transparent'"
                  @input="handleColorInput($event, v => { localStyles.borderColor = v; applyStyles() })"
                  class="w-10 h-8 cursor-pointer border-0 p-0.5 bg-transparent"
                  style="flex-shrink:0;min-width:40px;"
                />
                <input
                  :value="localStyles.borderColor || ''"
                  @input="handleColorInput($event, v => { localStyles.borderColor = v || undefined; applyStyles() })"
                  class="flex-1 h-8 px-2.5 text-xs text-white font-mono outline-none bg-[#112240]"
                  style="border:none!important;"
                  placeholder="transparent"
                />
              </div>
            </div>
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">边框宽度</label>
              <input
                v-model.number="localStyles.borderWidth"
                type="number"
                class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors"
                min="0"
                max="20"
                @change="applyStyles"
              />
            </div>
          </div>
        </div>

        <div class="border-t border-[#1e293b]" />

        <!-- 阴影 -->
        <div class="space-y-3">
          <h4 class="text-xs font-medium text-[#8892a0] uppercase tracking-wider">阴影</h4>
          <div>
            <label class="block text-xs text-[#5a6a80] mb-1">Box Shadow</label>
            <input
              v-model="localStyles.boxShadow"
              type="text"
              class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors font-mono"
              placeholder="0 4px 6px rgba(0,0,0,0.3)"
              @change="applyStyles"
            />
          </div>
        </div>
      </div>

      <!-- ═══════════════ 数据 Tab ═══════════════ -->
      <div v-if="activeTab === 'data'" class="p-4 space-y-4">
        <div class="space-y-3">
          <h4 class="text-xs font-medium text-[#8892a0] uppercase tracking-wider">数据源</h4>
          <div>
            <label class="block text-xs text-[#5a6a80] mb-1">数据源类型</label>
            <select
              class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors appearance-none cursor-pointer"
              :value="localDataSource?.type || 'static'"
              @change="applyDataSource(($event.target as HTMLSelectElement).value)"
            >
              <option value="static">静态数据</option>
              <option value="metric">系统指标</option>
              <option value="hourly">小时客流</option>
              <option value="device">设备数据</option>
            </select>
          </div>

          <!-- 指标选择 -->
          <div v-if="localDataSource?.type === 'metric'">
            <label class="block text-xs text-[#5a6a80] mb-1">选择指标</label>
            <div class="space-y-1 max-h-48 overflow-y-auto">
              <div
                v-for="opt in METRIC_OPTIONS"
                :key="opt.key"
                class="flex items-center gap-2 px-2.5 py-2 rounded-md cursor-pointer transition-colors"
                :class="localDataSource?.key === opt.key ? 'bg-[#172a45] border border-[#00d9ff]/20' : 'hover:bg-[#112240]'"
                @click="applyDataSourceKey(opt.key)"
              >
                <div class="w-3 h-3 rounded-full" :style="{ backgroundColor: opt.color }" />
                <span class="text-xs text-[#ccd6f6]">{{ opt.label }}</span>
              </div>
            </div>
          </div>

          <!-- 设备选择（仅视频组件） -->
          <div v-if="localDataSource?.type === 'device' && selectedComponent?.type === 'video'">
            <label class="block text-xs text-[#5a6a80] mb-1">选择设备</label>
            <select
              :value="localDataSource?.key || ''"
              class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors appearance-none cursor-pointer"
              @change="applyDataSourceKey(($event.target as HTMLSelectElement).value)"
            >
              <option value="">请选择设备</option>
              <option v-for="d in devices" :key="d.id" :value="d.id">
                {{ d.name }} ({{ d.status === 'online' ? '在线' : '离线' }})
              </option>
            </select>
            <p v-if="devices.length === 0 && !devicesLoading" class="text-xs text-[#5a6a80] mt-1">暂无设备</p>
            <p v-else-if="selectedDeviceName" class="text-xs text-[#00d9ff] mt-1">当前: {{ selectedDeviceName }}</p>
          </div>

          <div v-if="localDataSource?.type === 'static'" class="pt-2">
            <p class="text-xs text-[#5a6a80]">静态数据在组件属性 Tab 中配置</p>
          </div>
        </div>
      </div>

      <!-- ═══════════════ 属性 Tab ═══════════════ -->
      <div v-if="activeTab === 'props'" class="p-4 space-y-4">
        <!-- ── 边框容器专有属性 ── -->
        <template v-if="selectedComponent.type === 'border'">
          <div class="space-y-3">
            <h4 class="text-xs font-medium text-[#8892a0] uppercase tracking-wider">边框类型</h4>
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">边框样式</label>
              <select
                :value="localProps.borderType || 'dv-border-box-1'"
                class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors appearance-none cursor-pointer"
                @change="localProps.borderType = ($event.target as HTMLSelectElement).value; applyProps()"
              >
                <option value="dv-border-box-1">边框1</option>
                <option value="dv-border-box-2">边框2</option>
                <option value="dv-border-box-3">边框3</option>
                <option value="dv-border-box-4">边框4</option>
                <option value="dv-border-box-5">边框5</option>
                <option value="dv-border-box-6">边框6</option>
                <option value="dv-border-box-7">边框7</option>
                <option value="dv-border-box-8">边框8</option>
                <option value="dv-border-box-9">边框9</option>
                <option value="dv-border-box-10">边框10</option>
                <option value="dv-border-box-11">边框11</option>
                <option value="dv-border-box-12">边框12</option>
                <option value="dv-border-box-13">边框13</option>
              </select>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs text-[#5a6a80] mb-1">装饰线颜色1</label>
                <div class="flex items-center gap-0 rounded-md border border-[#1e293b] overflow-hidden">
                  <input
                    type="color"
                    :value="localProps.borderColors?.[0] || '#00d9ff'"
                    @input="handleColorInput($event, v => { if (!localProps.borderColors) localProps.borderColors = []; localProps.borderColors[0] = v; applyProps() })"
                    class="w-10 h-8 cursor-pointer border-0 p-0.5 bg-transparent"
                    style="flex-shrink:0;min-width:40px;"
                  />
                  <input
                    :value="localProps.borderColors?.[0] || ''"
                    @input="handleColorInput($event, v => { if (!localProps.borderColors) localProps.borderColors = []; localProps.borderColors[0] = v; applyProps() })"
                    class="flex-1 h-8 px-2.5 text-xs text-white font-mono outline-none bg-[#112240]"
                    style="border:none!important;"
                    placeholder="#00d9ff"
                  />
                </div>
              </div>
              <div>
                <label class="block text-xs text-[#5a6a80] mb-1">装饰线颜色2</label>
                <div class="flex items-center gap-0 rounded-md border border-[#1e293b] overflow-hidden">
                  <input
                    type="color"
                    :value="localProps.borderColors?.[1] || '#00d9ff'"
                    @input="handleColorInput($event, v => { if (!localProps.borderColors) localProps.borderColors = []; localProps.borderColors[1] = v; applyProps() })"
                    class="w-10 h-8 cursor-pointer border-0 p-0.5 bg-transparent"
                    style="flex-shrink:0;min-width:40px;"
                  />
                  <input
                    :value="localProps.borderColors?.[1] || ''"
                    @input="handleColorInput($event, v => { if (!localProps.borderColors) localProps.borderColors = []; localProps.borderColors[1] = v; applyProps() })"
                    class="flex-1 h-8 px-2.5 text-xs text-white font-mono outline-none bg-[#112240]"
                    style="border:none!important;"
                    placeholder="#00d9ff"
                  />
                </div>
              </div>
            </div>
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">边框背景色</label>
              <div class="flex items-center gap-0 rounded-md border border-[#1e293b] overflow-hidden">
                <input
                  type="color"
                  :value="localProps.backgroundColor || 'transparent'"
                  @input="handleColorInput($event, v => { localProps.backgroundColor = v; applyProps() })"
                  class="w-10 h-8 cursor-pointer border-0 p-0.5 bg-transparent"
                  style="flex-shrink:0;min-width:40px;"
                />
                <input
                  :value="localProps.backgroundColor || ''"
                  @input="handleColorInput($event, v => { localProps.backgroundColor = v || undefined; applyProps() })"
                  class="flex-1 h-8 px-2.5 text-xs text-white font-mono outline-none bg-[#112240]"
                  style="border:none!important;"
                  placeholder="transparent"
                />
              </div>
            </div>
          </div>
          <div class="border-t border-[#1e293b]" />
        </template>

        <!-- ── 装饰线专有属性 ── -->
        <template v-if="selectedComponent.type === 'decoration'">
          <div class="space-y-3">
            <h4 class="text-xs font-medium text-[#8892a0] uppercase tracking-wider">装饰类型</h4>
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">装饰样式</label>
              <select
                :value="localProps.decorationType || 'dv-decoration-1'"
                class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors appearance-none cursor-pointer"
                @change="localProps.decorationType = ($event.target as HTMLSelectElement).value; applyProps()"
              >
                <option value="dv-decoration-1">装饰1</option>
                <option value="dv-decoration-2">装饰2</option>
                <option value="dv-decoration-3">装饰3</option>
                <option value="dv-decoration-4">装饰4</option>
                <option value="dv-decoration-5">装饰5</option>
                <option value="dv-decoration-6">装饰6</option>
                <option value="dv-decoration-7">装饰7</option>
                <option value="dv-decoration-8">装饰8</option>
                <option value="dv-decoration-9">装饰9</option>
                <option value="dv-decoration-10">装饰10</option>
                <option value="dv-decoration-11">装饰11</option>
                <option value="dv-decoration-12">装饰12</option>
              </select>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs text-[#5a6a80] mb-1">装饰线颜色1</label>
                <div class="flex items-center gap-0 rounded-md border border-[#1e293b] overflow-hidden">
                  <input
                    type="color"
                    :value="localProps.decorationColors?.[0] || '#00d9ff'"
                    @input="handleColorInput($event, v => { if (!localProps.decorationColors) localProps.decorationColors = []; localProps.decorationColors[0] = v; applyProps() })"
                    class="w-10 h-8 cursor-pointer border-0 p-0.5 bg-transparent"
                    style="flex-shrink:0;min-width:40px;"
                  />
                  <input
                    :value="localProps.decorationColors?.[0] || ''"
                    @input="handleColorInput($event, v => { if (!localProps.decorationColors) localProps.decorationColors = []; localProps.decorationColors[0] = v; applyProps() })"
                    class="flex-1 h-8 px-2.5 text-xs text-white font-mono outline-none bg-[#112240]"
                    style="border:none!important;"
                    placeholder="#00d9ff"
                  />
                </div>
              </div>
              <div>
                <label class="block text-xs text-[#5a6a80] mb-1">装饰线颜色2</label>
                <div class="flex items-center gap-0 rounded-md border border-[#1e293b] overflow-hidden">
                  <input
                    type="color"
                    :value="localProps.decorationColors?.[1] || '#00d9ff'"
                    @input="handleColorInput($event, v => { if (!localProps.decorationColors) localProps.decorationColors = []; localProps.decorationColors[1] = v; applyProps() })"
                    class="w-10 h-8 cursor-pointer border-0 p-0.5 bg-transparent"
                    style="flex-shrink:0;min-width:40px;"
                  />
                  <input
                    :value="localProps.decorationColors?.[1] || ''"
                    @input="handleColorInput($event, v => { if (!localProps.decorationColors) localProps.decorationColors = []; localProps.decorationColors[1] = v; applyProps() })"
                    class="flex-1 h-8 px-2.5 text-xs text-white font-mono outline-none bg-[#112240]"
                    style="border:none!important;"
                    placeholder="#00d9ff"
                  />
                </div>
              </div>
            </div>
          </div>
          <div class="border-t border-[#1e293b]" />
        </template>

        <!-- ── Logo 专有属性 ── -->
        <template v-if="selectedComponent.type === 'logo'">
          <div class="space-y-3">
            <h4 class="text-xs font-medium text-[#8892a0] uppercase tracking-wider">Logo 设置</h4>
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">上传 Logo</label>
              <div class="w-full h-20 rounded-md border border-dashed border-[#1e293b] flex flex-col items-center justify-center gap-1 cursor-pointer hover:border-[#00d9ff]/30 transition-colors bg-[#112240]" @click="triggerLogoUpload">
                <svg class="w-6 h-6 text-[#5a6a80]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" /></svg>
                <span class="text-xs text-[#5a6a80]">点击上传图片</span>
              </div>
              <input ref="logoFileInput" type="file" accept="image/*" class="hidden" @change="handleLogoFileUpload" />
            </div>
            <div v-if="localProps.logoSrc">
              <label class="block text-xs text-[#5a6a80] mb-1">当前 Logo</label>
              <div class="relative w-full h-16 rounded-md border border-[#1e293b] overflow-hidden bg-[#112240] flex items-center justify-center p-1">
                <img :src="localProps.logoSrc" class="max-w-full max-h-full" style="object-fit: contain;" />
              </div>
              <button class="mt-2 w-full h-7 rounded-md bg-red-500/10 border border-red-500/30 text-xs text-red-400 hover:bg-red-500/20 cursor-pointer transition-colors" @click="localProps.logoSrc = ''; applyProps()">移除 Logo</button>
            </div>
          </div>
        </template>

        <!-- ── 指标卡片专有属性 ── -->
        <template v-if="selectedComponent.type === 'metric-card' || selectedComponent.type === 'counter'">
          <div class="space-y-3">
            <h4 class="text-xs font-medium text-[#8892a0] uppercase tracking-wider">标题样式</h4>
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">标题文本</label>
              <input
                :value="localProps.title"
                type="text"
                class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors"
                @change="localProps.title = ($event.target as HTMLInputElement).value; applyProps()"
              />
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs text-[#5a6a80] mb-1">字体大小</label>
                <input
                  :value="localProps.titleFontSize ?? 14"
                  type="number"
                  min="10"
                  max="64"
                  class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors"
                  @change="localProps.titleFontSize = Number(($event.target as HTMLInputElement).value); applyProps()"
                />
              </div>
              <div>
                <label class="block text-xs text-[#5a6a80] mb-1">加粗</label>
                <div class="flex h-8 items-center">
                  <label class="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      :checked="localProps.titleBold ?? false"
                      class="w-4 h-4 rounded border-[#2d4765] accent-[#00d9ff]"
                      @change="localProps.titleBold = ($event.target as HTMLInputElement).checked; applyProps()"
                    />
                    <span class="text-xs text-white">加粗</span>
                  </label>
                </div>
              </div>
            </div>
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">对齐方式</label>
              <select
                :value="localProps.titleAlign || 'center'"
                class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors appearance-none cursor-pointer"
                @change="localProps.titleAlign = ($event.target as HTMLSelectElement).value; applyProps()"
              >
                <option value="center">居中</option>
                <option value="left">靠左</option>
                <option value="right">靠右</option>
              </select>
            </div>
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">布局方式</label>
              <select
                :value="localProps.layout || 'vertical'"
                class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors appearance-none cursor-pointer"
                @change="localProps.layout = ($event.target as HTMLSelectElement).value; applyProps()"
              >
                <option value="vertical">上下排列（文字在上）</option>
                <option value="horizontal">左右排列（文字在左）</option>
              </select>
            </div>
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">标题颜色</label>
              <div class="flex items-center gap-0 rounded-md border border-[#1e293b] overflow-hidden">
                <input type="color" :value="localProps.titleColor || '#00d9ff'"
                  @input="handleColorInput($event, v => { localProps.titleColor = v; applyProps() })"
                  class="w-10 h-8 cursor-pointer border-0 p-0.5 bg-transparent"
                  style="flex-shrink:0;min-width:40px;" />
                <input :value="localProps.titleColor || ''"
                  @input="handleColorInput($event, v => { localProps.titleColor = v; applyProps() })"
                  class="flex-1 h-8 px-2.5 text-xs text-white font-mono outline-none bg-[#112240]"
                  style="border:none!important;" placeholder="#00d9ff" />
              </div>
            </div>
          </div>
          <div class="border-t border-[#1e293b]" />
        </template>

        <!-- ── 排名计数器专有属性 ── -->
        <template v-if="selectedComponent.type === 'ranking-counter'">
          <div class="space-y-3">
            <h4 class="text-xs font-medium text-[#8892a0] uppercase tracking-wider">排名设置</h4>
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">左侧文字</label>
              <input :value="localProps.leftText || '您是第'" type="text"
                class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors"
                @change="localProps.leftText = ($event.target as HTMLInputElement).value; applyProps()" />
            </div>
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">右侧文字</label>
              <input :value="localProps.rightText || '位到访的客户'" type="text"
                class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors"
                @change="localProps.rightText = ($event.target as HTMLInputElement).value; applyProps()" />
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs text-[#5a6a80] mb-1">数字位数</label>
                <input :value="localProps.digits ?? 6" type="number" min="3" max="12"
                  class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors"
                  @change="localProps.digits = Number(($event.target as HTMLInputElement).value); applyProps()" />
              </div>
              <div>
                <label class="block text-xs text-[#5a6a80] mb-1">字体大小</label>
                <input :value="localProps.counterFontSize ?? 20" type="number" min="12" max="64"
                  class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors"
                  @change="localProps.counterFontSize = Number(($event.target as HTMLInputElement).value); applyProps()" />
              </div>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs text-[#5a6a80] mb-1">文字颜色</label>
                <div class="flex items-center gap-0 rounded-md border border-[#1e293b] overflow-hidden">
                  <input type="color" :value="localProps.textColor || '#ffffff'"
                    @input="handleColorInput($event, v => { localProps.textColor = v; applyProps() })"
                    class="w-10 h-8 cursor-pointer border-0 p-0.5 bg-transparent" style="flex-shrink:0;min-width:40px;" />
                  <input :value="localProps.textColor || ''"
                    @input="handleColorInput($event, v => { localProps.textColor = v; applyProps() })"
                    class="flex-1 h-8 px-2.5 text-xs text-white font-mono outline-none bg-[#112240]" style="border:none!important;" placeholder="#ffffff" />
                </div>
              </div>
              <div>
                <label class="block text-xs text-[#5a6a80] mb-1">数字颜色</label>
                <div class="flex items-center gap-0 rounded-md border border-[#1e293b] overflow-hidden">
                  <input type="color" :value="localProps.counterColor || '#00d9ff'"
                    @input="handleColorInput($event, v => { localProps.counterColor = v; applyProps() })"
                    class="w-10 h-8 cursor-pointer border-0 p-0.5 bg-transparent" style="flex-shrink:0;min-width:40px;" />
                  <input :value="localProps.counterColor || ''"
                    @input="handleColorInput($event, v => { localProps.counterColor = v; applyProps() })"
                    class="flex-1 h-8 px-2.5 text-xs text-white font-mono outline-none bg-[#112240]" style="border:none!important;" placeholder="#00d9ff" />
                </div>
              </div>
            </div>
          </div>
          <div class="border-t border-[#1e293b]" />
        </template>

        <!-- ── 线条专有属性 ── -->
        <template v-if="selectedComponent.type === 'line'">
          <div class="space-y-3">
            <h4 class="text-xs font-medium text-[#8892a0] uppercase tracking-wider">线条设置</h4>
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">方向</label>
              <select
                :value="localProps.direction || 'horizontal'"
                class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors appearance-none cursor-pointer"
                @change="localProps.direction = ($event.target as HTMLSelectElement).value; applyProps()"
              >
                <option value="horizontal">横向</option>
                <option value="vertical">竖向</option>
              </select>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs text-[#5a6a80] mb-1">线条粗细</label>
                <input
                  :value="localProps.thickness ?? 2"
                  type="number"
                  min="1"
                  max="50"
                  class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors"
                  @change="localProps.thickness = Number(($event.target as HTMLInputElement).value); applyProps()"
                />
              </div>
              <div>
                <label class="block text-xs text-[#5a6a80] mb-1">透明度</label>
                <div class="flex items-center gap-2">
                  <input
                    :value="localProps.lineOpacity ?? 1"
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    class="flex-1 accent-[#00d9ff]"
                    @change="localProps.lineOpacity = Number(($event.target as HTMLInputElement).value); applyProps()"
                  />
                  <span class="text-xs text-white font-mono w-8 text-right">{{ Math.round((localProps.lineOpacity ?? 1) * 100) }}%</span>
                </div>
              </div>
            </div>
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">线条颜色</label>
              <div class="flex items-center gap-0 rounded-md border border-[#1e293b] overflow-hidden">
                <input type="color" :value="localProps.lineColor || '#00d9ff'"
                  @input="handleColorInput($event, v => { localProps.lineColor = v; applyProps() })"
                  class="w-10 h-8 cursor-pointer border-0 p-0.5 bg-transparent"
                  style="flex-shrink:0;min-width:40px;" />
                <input :value="localProps.lineColor || ''"
                  @input="handleColorInput($event, v => { localProps.lineColor = v; applyProps() })"
                  class="flex-1 h-8 px-2.5 text-xs text-white font-mono outline-none bg-[#112240]"
                  style="border:none!important;" placeholder="#00d9ff" />
              </div>
            </div>
          </div>
          <div class="border-t border-[#1e293b]" />
        </template>

        <!-- ── 视频墙专有属性 ── -->
        <template v-if="selectedComponent.type === 'video-wall'">
          <div class="space-y-3">
            <h4 class="text-xs font-medium text-[#8892a0] uppercase tracking-wider">视频墙设置</h4>

            <!-- 宫格布局 -->
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">宫格布局</label>
              <select
                :value="`${localProps.gridCols || 2}x${localProps.gridRows || 1}`"
                class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors appearance-none cursor-pointer"
                @change="(e) => {
                  const [cols, rows] = (e.target as HTMLSelectElement).value.split('x').map(Number)
                  localProps.gridCols = cols
                  localProps.gridRows = rows
                  syncVideoWallArrays(cols * rows)
                }"
              >
                <option value="1x1">1 宫格 (1x1)</option>
                <option value="2x1">2 宫格 (1行2列)</option>
                <option value="2x2">4 宫格 (2x2)</option>
                <option value="3x2">6 宫格 (3列2行)</option>
                <option value="4x2">8 宫格 (4列2行)</option>
                <option value="3x3">9 宫格 (3x3)</option>
              </select>
            </div>

            <!-- 每个格子的设备选择 -->
            <div v-for="(deviceId, index) in getVideoWallDeviceIds()" :key="index">
              <label class="block text-xs text-[#5a6a80] mb-1">格子 {{ index + 1 }} 选择设备</label>
              <select
                :value="deviceId || ''"
                class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors appearance-none cursor-pointer"
                @change="(e) => updateVideoWallCell(index, (e.target as HTMLSelectElement).value)"
              >
                <option value="">请选择设备</option>
                <option v-for="d in devices" :key="d.id" :value="d.id">
                  {{ d.name }} - {{ d.ip }}
                </option>
              </select>
              <p v-if="devices.length === 0" class="text-xs text-[#5a6a80] mt-1">
                暂无设备，请先在设备管理中添加
              </p>
            </div>

            <!-- 自动播放和静音 -->
            <div class="flex items-center gap-4">
              <label class="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  :checked="localProps.autoPlay ?? true"
                  class="w-4 h-4 rounded border-[#2d4765] accent-[#00d9ff]"
                  @change="localProps.autoPlay = ($event.target as HTMLInputElement).checked; applyProps()"
                />
                <span class="text-xs text-white">自动播放</span>
              </label>
              <label class="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  :checked="localProps.muted ?? true"
                  class="w-4 h-4 rounded border-[#2d4765] accent-[#00d9ff]"
                  @change="localProps.muted = ($event.target as HTMLInputElement).checked; applyProps()"
                />
                <span class="text-xs text-white">静音</span>
              </label>
            </div>

            <!-- 边框样式 -->
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs text-[#5a6a80] mb-1">格子边框宽度</label>
                <input
                  :value="localProps.cellBorderWidth ?? 1"
                  type="number"
                  min="0"
                  max="10"
                  class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors"
                  @change="localProps.cellBorderWidth = Number(($event.target as HTMLInputElement).value); applyProps()"
                />
              </div>
              <div>
                <label class="block text-xs text-[#5a6a80] mb-1">格子边框颜色</label>
                <div class="flex items-center gap-0 rounded-md border border-[#1e293b] overflow-hidden">
                  <input type="color" :value="localProps.cellBorderColor || '#1e293b'"
                    @input="handleColorInput($event, v => { localProps.cellBorderColor = v; applyProps() })"
                    class="w-10 h-8 cursor-pointer border-0 p-0.5 bg-transparent"
                    style="flex-shrink:0;min-width:40px;" />
                  <input :value="localProps.cellBorderColor || ''"
                    @input="handleColorInput($event, v => { localProps.cellBorderColor = v; applyProps() })"
                    class="flex-1 h-8 px-2.5 text-xs text-white font-mono outline-none bg-[#112240]"
                    style="border:none!important;" placeholder="#1e293b" />
                </div>
              </div>
            </div>

            <!-- 无视频时的背景色 -->
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">无视频源背景色</label>
              <div class="flex items-center gap-0 rounded-md border border-[#1e293b] overflow-hidden">
                <input type="color" :value="localProps.placeholderBg || '#0d1421'"
                  @input="handleColorInput($event, v => { localProps.placeholderBg = v; applyProps() })"
                  class="w-10 h-8 cursor-pointer border-0 p-0.5 bg-transparent"
                  style="flex-shrink:0;min-width:40px;" />
                <input :value="localProps.placeholderBg || ''"
                  @input="handleColorInput($event, v => { localProps.placeholderBg = v; applyProps() })"
                  class="flex-1 h-8 px-2.5 text-xs text-white font-mono outline-none bg-[#112240]"
                  style="border:none!important;" placeholder="#0d1421" />
              </div>
            </div>
          </div>
          <div class="border-t border-[#1e293b]" />
        </template>

        <!-- ── 通用组件属性 ── -->
        <div class="space-y-3">
          <h4 class="text-xs font-medium text-[#8892a0] uppercase tracking-wider">组件属性</h4>
          <div
            v-for="(val, key) in localProps"
            :key="key"
            class="flex items-center gap-2"
          >
            <label class="text-xs text-[#5a6a80] w-20 flex-shrink-0 truncate">{{ key }}</label>
            <input
              :value="typeof val === 'object' ? JSON.stringify(val) : String(val)"
              type="text"
              class="flex-1 h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors"
              @change="localProps[key] = ($event.target as HTMLInputElement).value; applyProps()"
            />
          </div>
          <div v-if="Object.keys(localProps).length === 0" class="text-xs text-[#5a6a80] py-4 text-center">
            此组件无额外属性
          </div>
        </div>
      </div>

      <!-- ═══════════════ 动画 Tab ═══════════════ -->
      <div v-if="activeTab === 'animation'" class="p-4 space-y-4">
        <div class="space-y-3">
          <h4 class="text-xs font-medium text-[#8892a0] uppercase tracking-wider">动画效果</h4>
          <div>
            <label class="block text-xs text-[#5a6a80] mb-1">动画类型</label>
            <select
              v-model="localAnimation.type"
              class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors appearance-none cursor-pointer"
              @change="applyAnimation"
            >
              <option
                v-for="preset in animationPresets"
                :key="preset.value"
                :value="preset.value"
              >
                {{ preset.label }}
              </option>
            </select>
          </div>

          <template v-if="localAnimation.type !== 'none'">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs text-[#5a6a80] mb-1">持续时间 (ms)</label>
                <input
                  v-model.number="localAnimation.duration"
                  type="number"
                  class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors"
                  min="100"
                  max="10000"
                  step="100"
                  @change="applyAnimation"
                />
              </div>
              <div>
                <label class="block text-xs text-[#5a6a80] mb-1">延迟 (ms)</label>
                <input
                  v-model.number="localAnimation.delay"
                  type="number"
                  class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors"
                  min="0"
                  max="10000"
                  step="100"
                  @change="applyAnimation"
                />
              </div>
            </div>
            <div>
              <label class="block text-xs text-[#5a6a80] mb-1">重复</label>
              <select
                v-model="localAnimation.repeat"
                class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors appearance-none cursor-pointer"
                @change="applyAnimation"
              >
                <option :value="1">1 次</option>
                <option :value="2">2 次</option>
                <option :value="3">3 次</option>
                <option :value="5">5 次</option>
                <option :value="10">10 次</option>
                <option value="infinite">无限循环</option>
              </select>
            </div>
          </template>
        </div>
      </div>

      <!-- ═══════════════ 高级 Tab ═══════════════ -->
      <div v-if="activeTab === 'advanced'" class="p-4 space-y-4">
        <!-- 模板编辑模式入口 -->
        <div class="space-y-3">
          <h4 class="text-xs font-medium text-[#8892a0] uppercase tracking-wider">画布配置</h4>
          <button
            class="w-full flex items-center justify-center gap-2 h-9 rounded-md bg-[#0a192f] border border-[#1e293b] text-xs text-[#ccd6f6] hover:border-[#00d9ff]/30 cursor-pointer transition-colors"
            @click="emit('toggle-template-edit-mode')"
          >
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
              <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
            </svg>
            编辑画布配置
          </button>
        </div>

        <div class="border-t border-[#1e293b]" />

        <!-- 组件信息 -->
        <div class="space-y-3">
          <h4 class="text-xs font-medium text-[#8892a0] uppercase tracking-wider">组件信息</h4>
          <div class="space-y-2">
            <div class="flex items-center gap-2">
              <span class="text-xs text-[#5a6a80] w-16">ID</span>
              <span class="text-xs text-[#ccd6f6] font-mono truncate">{{ selectedComponent.id }}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-xs text-[#5a6a80] w-16">类型</span>
              <span class="text-xs text-[#ccd6f6]">{{ selectedComponent.type }}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-xs text-[#5a6a80] w-16">层级</span>
              <span class="text-xs text-[#ccd6f6]">Z: {{ selectedComponent.zIndex }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.property-panel {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.property-panel::-webkit-scrollbar {
  width: 4px;
}

.property-panel::-webkit-scrollbar-track {
  background: transparent;
}

.property-panel::-webkit-scrollbar-thumb {
  background: #1e293b;
  border-radius: 2px;
}

input[type='range'] {
  -webkit-appearance: none;
  appearance: none;
  height: 4px;
  border-radius: 2px;
  background: #1e293b;
  outline: none;
}

input[type='range']::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #00d9ff;
  cursor: pointer;
  border: 2px solid #0a192f;
}
</style>
