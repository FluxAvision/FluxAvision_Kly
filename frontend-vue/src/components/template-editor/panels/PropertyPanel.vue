<script setup lang="ts">
/**
 * 属性面板 - 右侧属性编辑
 */
import { computed, watch, ref, onMounted } from 'vue'
import { Trash2, Lock, Unlock, Eye, EyeOff } from 'lucide-vue-next'
import type { ComponentConfig } from '@/types/template-editor'
import { METRIC_OPTIONS } from '@/types/template-editor'

interface Device {
  id: string
  name: string
  status: string
  ip?: string
  location?: string
}

const props = defineProps<{
  component: ComponentConfig | null
}>()

const emit = defineEmits<{
  update: [id: string, updates: Partial<ComponentConfig>]
  delete: [id: string]
}>()

// 设备列表
const devices = ref<Device[]>([])

// 本地编辑状态
const localConfig = computed(() => props.component ? { ...props.component } : null)

// 获取设备列表
async function fetchDevices() {
  try {
    const res = await fetch('/api/devices')
    if (res.ok) {
      const json = await res.json()
      devices.value = json.data || json || []
    }
  } catch {
    devices.value = []
  }
}

// 更新属性
function updateProp(key: string, value: any) {
  if (!props.component) return
  emit('update', props.component.id, { props: { ...props.component.props, [key]: value } })
}

// 更新样式
function updateStyle(key: string, value: any) {
  if (!props.component) return
  emit('update', props.component.id, { styles: { ...props.component.styles, [key]: value } })
}

// 更新位置/大小
function updatePosition(key: string, value: number) {
  if (!props.component) return
  emit('update', props.component.id, { [key]: value })
}

// 更新数据源
function updateDataSource(key: string, value: any) {
  if (!props.component) return
  const currentDataSource = props.component.dataSource || { type: 'device' }
  emit('update', props.component.id, {
    dataSource: { ...currentDataSource, [key]: value }
  })
}

// 选择设备时自动设置数据源类型
function handleDeviceSelect(deviceId: string) {
  if (!props.component) return
  emit('update', props.component.id, {
    dataSource: { type: 'device', key: deviceId }
  })
}

// 切换锁定
function toggleLock() {
  if (!props.component) return
  emit('update', props.component.id, { locked: !props.component.locked })
}

// 切换可见
function toggleVisible() {
  if (!props.component) return
  emit('update', props.component.id, { visible: !props.component.visible })
}

// 删除组件
function handleDelete() {
  if (!props.component) return
  emit('delete', props.component.id)
}

// 获取选中的设备名称
const selectedDeviceName = computed(() => {
  if (!props.component?.dataSource?.key) return null
  const device = devices.value.find(d => d.id === props.component?.dataSource?.key)
  return device?.name || null
})

// 边框类型选项
const borderTypes = [
  { value: 'dv-border-box-1', label: '边框1' },
  { value: 'dv-border-box-2', label: '边框2' },
  { value: 'dv-border-box-3', label: '边框3' },
  { value: 'dv-border-box-4', label: '边框4' },
  { value: 'dv-border-box-5', label: '边框5' },
  { value: 'dv-border-box-6', label: '边框6' },
  { value: 'dv-border-box-7', label: '边框7' },
  { value: 'dv-border-box-8', label: '边框8' },
  { value: 'dv-border-box-9', label: '边框9' },
  { value: 'dv-border-box-10', label: '边框10' },
  { value: 'dv-border-box-11', label: '边框11' },
  { value: 'dv-border-box-12', label: '边框12' },
  { value: 'dv-border-box-13', label: '边框13' },
]

// 装饰类型选项
const decorationTypes = [
  { value: 'dv-decoration-1', label: '装饰1' },
  { value: 'dv-decoration-2', label: '装饰2' },
  { value: 'dv-decoration-3', label: '装饰3' },
  { value: 'dv-decoration-4', label: '装饰4' },
  { value: 'dv-decoration-5', label: '装饰5' },
  { value: 'dv-decoration-6', label: '装饰6' },
  { value: 'dv-decoration-7', label: '装饰7' },
  { value: 'dv-decoration-8', label: '装饰8' },
  { value: 'dv-decoration-9', label: '装饰9' },
  { value: 'dv-decoration-10', label: '装饰10' },
  { value: 'dv-decoration-11', label: '装饰11' },
  { value: 'dv-decoration-12', label: '装饰12' },
]

// 组件挂载时获取设备列表
onMounted(() => {
  fetchDevices()
})
</script>

<template>
  <div class="property-panel h-full overflow-y-auto bg-[#0a192f] border-l border-[#1e293b]">
    <!-- 无选中状态 -->
    <div v-if="!component" class="p-4 text-center text-[#8892a0] text-sm">
      请选择组件进行编辑
    </div>

    <!-- 编辑面板 -->
    <div v-else class="p-4 space-y-4">
      <!-- 标题栏 -->
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-medium text-white">{{ component.name }}</h3>
        <div class="flex items-center gap-1">
          <button
            class="p-1.5 rounded hover:bg-white/10 transition-colors cursor-pointer"
            :class="component.locked ? 'text-[#00d9ff]' : 'text-[#8892a0]'"
            @click="toggleLock"
          >
            <Lock v-if="component.locked" class="w-4 h-4" />
            <Unlock v-else class="w-4 h-4" />
          </button>
          <button
            class="p-1.5 rounded hover:bg-white/10 transition-colors cursor-pointer"
            :class="!component.visible ? 'text-[#ef4444]' : 'text-[#8892a0]'"
            @click="toggleVisible"
          >
            <EyeOff v-if="!component.visible" class="w-4 h-4" />
            <Eye v-else class="w-4 h-4" />
          </button>
          <button
            class="p-1.5 rounded hover:bg-white/10 text-[#ef4444] transition-colors cursor-pointer"
            @click="handleDelete"
          >
            <Trash2 class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- 位置/大小 -->
      <div class="space-y-2">
        <h4 class="text-xs text-[#8892a0]">位置与大小</h4>
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="text-xs text-[#8892a0]">X</label>
            <input
              type="number"
              :value="component.x"
              class="w-full bg-[#112240] border border-[#1e293b] rounded px-2 py-1 text-sm text-white"
              @input="(e) => updatePosition('x', Number((e.target as HTMLInputElement).value))"
            />
          </div>
          <div>
            <label class="text-xs text-[#8892a0]">Y</label>
            <input
              type="number"
              :value="component.y"
              class="w-full bg-[#112240] border border-[#1e293b] rounded px-2 py-1 text-sm text-white"
              @input="(e) => updatePosition('y', Number((e.target as HTMLInputElement).value))"
            />
          </div>
          <div>
            <label class="text-xs text-[#8892a0]">宽度</label>
            <input
              type="number"
              :value="component.width"
              class="w-full bg-[#112240] border border-[#1e293b] rounded px-2 py-1 text-sm text-white"
              @input="(e) => updatePosition('width', Number((e.target as HTMLInputElement).value))"
            />
          </div>
          <div>
            <label class="text-xs text-[#8892a0]">高度</label>
            <input
              type="number"
              :value="component.height"
              class="w-full bg-[#112240] border border-[#1e293b] rounded px-2 py-1 text-sm text-white"
              @input="(e) => updatePosition('height', Number((e.target as HTMLInputElement).value))"
            />
          </div>
        </div>
      </div>

      <!-- 组件特定属性 -->
      <div v-if="component.type === 'border'" class="space-y-2">
        <h4 class="text-xs text-[#8892a0]">边框设置</h4>
        <select
          :value="component.props?.borderType"
          class="w-full bg-[#112240] border border-[#1e293b] rounded px-2 py-1.5 text-sm text-white"
          @change="(e) => updateProp('borderType', (e.target as HTMLSelectElement).value)"
        >
          <option v-for="bt in borderTypes" :key="bt.value" :value="bt.value">{{ bt.label }}</option>
        </select>
        <div class="mt-2">
          <label class="text-xs text-[#8892a0]">装饰线颜色1</label>
          <input type="color" :value="component.props?.borderColors?.[0] || '#00d9ff'"
            class="w-full h-8 bg-[#112240] border border-[#1e293b] rounded"
            @input="(e) => updateProp('borderColors', [($event.target as HTMLInputElement).value, component.props?.borderColors?.[1] || '#1e3a5f'])" />
        </div>
        <div class="mt-2">
          <label class="text-xs text-[#8892a0]">装饰线颜色2</label>
          <input type="color" :value="component.props?.borderColors?.[1] || '#1e3a5f'"
            class="w-full h-8 bg-[#112240] border border-[#1e293b] rounded"
            @input="(e) => updateProp('borderColors', [component.props?.borderColors?.[0] || '#00d9ff', ($event.target as HTMLInputElement).value])" />
        </div>
        <div class="mt-2">
          <label class="text-xs text-[#8892a0]">边框背景色</label>
          <input type="color" :value="component.styles?.backgroundColor || '#1e3a5f'"
            class="w-full h-8 bg-[#112240] border border-[#1e293b] rounded"
            @input="(e) => updateStyle('backgroundColor', ($event.target as HTMLInputElement).value)" />
        </div>
      </div>

      <div v-if="component.type === 'decoration'" class="space-y-2">
        <h4 class="text-xs text-[#8892a0]">装饰设置</h4>
        <select
          :value="component.props?.decorationType"
          class="w-full bg-[#112240] border border-[#1e293b] rounded px-2 py-1.5 text-sm text-white"
          @change="(e) => updateProp('decorationType', (e.target as HTMLSelectElement).value)"
        >
          <option v-for="dt in decorationTypes" :key="dt.value" :value="dt.value">{{ dt.label }}</option>
        </select>
        <div class="mt-2">
          <label class="text-xs text-[#8892a0]">装饰线颜色1</label>
          <input type="color" :value="component.props?.decorationColors?.[0] || '#00d9ff'"
            class="w-full h-8 bg-[#112240] border border-[#1e293b] rounded"
            @input="(e) => updateProp('decorationColors', [($event.target as HTMLInputElement).value, component.props?.decorationColors?.[1] || '#1e3a5f'])" />
        </div>
        <div class="mt-2">
          <label class="text-xs text-[#8892a0]">装饰线颜色2</label>
          <input type="color" :value="component.props?.decorationColors?.[1] || '#1e3a5f'"
            class="w-full h-8 bg-[#112240] border border-[#1e293b] rounded"
            @input="(e) => updateProp('decorationColors', [component.props?.decorationColors?.[0] || '#00d9ff', ($event.target as HTMLInputElement).value])" />
        </div>
      </div>

      <div v-if="component.type === 'metric-card' || component.type === 'counter'" class="space-y-2">
        <h4 class="text-xs text-[#8892a0]">卡片设置</h4>
        <div>
          <label class="text-xs text-[#8892a0]">标题</label>
          <input
            type="text"
            :value="component.props?.title"
            class="w-full bg-[#112240] border border-[#1e293b] rounded px-2 py-1 text-sm text-white"
            @input="(e) => updateProp('title', (e.target as HTMLInputElement).value)"
          />
        </div>
        <div v-if="component.type === 'counter'" class="mt-2">
          <label class="text-xs text-[#8892a0]">数字位数</label>
          <input
            type="number"
            :value="component.props?.digits || 8"
            min="1"
            max="12"
            class="w-full bg-[#112240] border border-[#1e293b] rounded px-2 py-1 text-sm text-white"
            @input="(e) => updateProp('digits', Number((e.target as HTMLInputElement).value))"
          />
        </div>
        <h4 class="text-xs text-[#8892a0] mt-3">文本样式</h4>
        <div class="mt-2">
          <label class="text-xs text-[#8892a0]">字体大小</label>
          <input type="number" :value="component.styles?.fontSize || 24" min="12" max="128"
            class="w-full bg-[#112240] border border-[#1e293b] rounded px-2 py-1 text-sm text-white"
            @input="(e) => updateStyle('fontSize', Number(($event.target as HTMLInputElement).value))" />
        </div>
        <div class="mt-2">
          <label class="text-xs text-[#8892a0]">字体颜色</label>
          <input type="color" :value="component.styles?.color || '#ffffff'"
            class="w-full h-8 bg-[#112240] border border-[#1e293b] rounded"
            @input="(e) => updateStyle('color', ($event.target as HTMLInputElement).value)" />
        </div>
      </div>

      <!-- ── 指标卡片专有属性 ── -->
      <div v-if="component.type === 'metric-card'" class="space-y-3">
        <h4 class="text-xs font-medium text-[#8892a0] uppercase tracking-wider">标题样式</h4>
        <div>
          <label class="block text-xs text-[#5a6a80] mb-1">标题</label>
          <input
            :value="component.props?.title"
            type="text"
            class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors"
            @input="(e) => updateProp('title', (e.target as HTMLInputElement).value)"
          />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs text-[#5a6a80] mb-1">字体大小</label>
            <input
              :value="component.props?.titleFontSize ?? 14"
              type="number"
              min="10"
              max="64"
              class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors"
              @input="(e) => updateProp('titleFontSize', Number(($event.target as HTMLInputElement).value))"
            />
          </div>
          <div>
            <label class="block text-xs text-[#5a6a80] mb-1">加粗</label>
            <div class="flex h-8 items-center">
              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  :checked="component.props?.titleBold ?? false"
                  class="w-4 h-4 rounded border-[#2d4765] accent-[#00d9ff]"
                  @change="(e) => updateProp('titleBold', (e.target as HTMLInputElement).checked)"
                />
                <span class="text-xs text-white">加粗</span>
              </label>
            </div>
          </div>
        </div>
        <div>
          <label class="block text-xs text-[#5a6a80] mb-1">对齐方式</label>
          <select
            :value="component.props?.titleAlign || 'center'"
            class="w-full h-8 rounded-md bg-[#112240] border border-[#1e293b] px-2.5 text-xs text-white outline-none focus:border-[#00d9ff] transition-colors appearance-none cursor-pointer"
            @change="(e) => updateProp('titleAlign', (e.target as HTMLSelectElement).value)"
          >
            <option value="center">居中</option>
            <option value="left">靠左</option>
            <option value="right">靠右</option>
          </select>
        </div>
        <div>
          <label class="block text-xs text-[#5a6a80] mb-1">标题背景色</label>
          <div class="flex items-center gap-0 rounded-md border border-[#1e293b] overflow-hidden">
            <input type="color" :value="component.props?.titleBgColor || '#00d9ff'"
              @input="(e) => updateProp('titleBgColor', ($event.target as HTMLInputElement).value)"
              class="w-10 h-8 cursor-pointer border-0 p-0.5 bg-transparent"
              style="flex-shrink:0;min-width:40px;" />
            <input :value="component.props?.titleBgColor || ''"
              @input="(e) => updateProp('titleBgColor', (e.target as HTMLInputElement).value || '')"
              class="flex-1 h-8 px-2.5 text-xs text-white font-mono outline-none bg-[#112240]"
              style="border:none!important;" placeholder="默认渐变" />
          </div>
        </div>
      </div>
      <div v-if="component.type === 'metric-card'" class="border-t border-[#1e293b]" />

      <div v-if="component.type === 'chart-line' || component.type === 'chart-bar'" class="space-y-2">
        <h4 class="text-xs text-[#8892a0]">图表设置</h4>
        <div>
          <label class="text-xs text-[#8892a0]">标题</label>
          <input
            type="text"
            :value="component.props?.title"
            class="w-full bg-[#112240] border border-[#1e293b] rounded px-2 py-1 text-sm text-white"
            @input="(e) => updateProp('title', (e.target as HTMLInputElement).value)"
          />
        </div>
        <div class="flex gap-4 mt-2">
          <label class="flex items-center gap-1.5 text-xs text-[#8892a0]">
            <input
              type="checkbox"
              :checked="component.props?.showIn ?? true"
              @change="(e) => updateProp('showIn', (e.target as HTMLInputElement).checked)"
              class="accent-[#00d9ff]"
            />
            显示进入
          </label>
          <label class="flex items-center gap-1.5 text-xs text-[#8892a0]">
            <input
              type="checkbox"
              :checked="component.props?.showOut ?? true"
              @change="(e) => updateProp('showOut', (e.target as HTMLInputElement).checked)"
              class="accent-[#00d9ff]"
            />
            显示出去
          </label>
        </div>
      </div>

      <div v-if="component.type === 'video'" class="space-y-2">
        <h4 class="text-xs text-[#8892a0]">视频设置</h4>
        <div class="flex gap-4">
          <label class="flex items-center gap-1.5 text-xs text-[#8892a0]">
            <input
              type="checkbox"
              :checked="component.props?.showName ?? true"
              @change="(e) => updateProp('showName', (e.target as HTMLInputElement).checked)"
              class="accent-[#00d9ff]"
            />
            显示名称
          </label>
          <label class="flex items-center gap-1.5 text-xs text-[#8892a0]">
            <input
              type="checkbox"
              :checked="component.props?.autoPlay ?? true"
              @change="(e) => updateProp('autoPlay', (e.target as HTMLInputElement).checked)"
              class="accent-[#00d9ff]"
            />
            自动播放
          </label>
        </div>
      </div>

      <div v-if="component.type === 'title' || component.type === 'text'" class="space-y-2">
        <h4 class="text-xs text-[#8892a0]">文本设置</h4>
        <div>
          <label class="text-xs text-[#8892a0]">文本内容</label>
          <input
            type="text"
            :value="component.props?.text"
            class="w-full bg-[#112240] border border-[#1e293b] rounded px-2 py-1 text-sm text-white"
            @input="(e) => updateProp('text', (e.target as HTMLInputElement).value)"
          />
        </div>
        <div v-if="component.type === 'title'" class="mt-2">
          <label class="text-xs text-[#8892a0]">级别</label>
          <select
            :value="component.props?.level || 1"
            class="w-full bg-[#112240] border border-[#1e293b] rounded px-2 py-1.5 text-sm text-white"
            @change="(e) => updateProp('level', Number((e.target as HTMLSelectElement).value))"
          >
            <option :value="1">H1 - 大标题</option>
            <option :value="2">H2 - 中标题</option>
            <option :value="3">H3 - 小标题</option>
          </select>
        </div>
        <div class="mt-2">
          <label class="text-xs text-[#8892a0]">字体大小</label>
          <input type="number" :value="component.styles?.fontSize || 24" min="12" max="128"
            class="w-full bg-[#112240] border border-[#1e293b] rounded px-2 py-1 text-sm text-white"
            @input="(e) => updateStyle('fontSize', Number(($event.target as HTMLInputElement).value))" />
        </div>
        <div class="mt-2">
          <label class="text-xs text-[#8892a0]">字体颜色</label>
          <input type="color" :value="component.styles?.color || '#ffffff'"
            class="w-full h-8 bg-[#112240] border border-[#1e293b] rounded"
            @input="(e) => updateStyle('color', ($event.target as HTMLInputElement).value)" />
        </div>
        <div class="mt-2">
          <label class="text-xs text-[#8892a0]">字体粗细</label>
          <select :value="component.styles?.fontWeight || 'normal'"
            class="w-full bg-[#112240] border border-[#1e293b] rounded px-2 py-1.5 text-sm text-white"
            @change="(e) => updateStyle('fontWeight', ($event.target as HTMLSelectElement).value)">
            <option value="normal">常规</option>
            <option value="bold">加粗</option>
            <option value="lighter">细体</option>
          </select>
        </div>
        <div class="mt-2">
          <label class="text-xs text-[#8892a0]">文字对齐</label>
          <select :value="component.styles?.textAlign || 'center'"
            class="w-full bg-[#112240] border border-[#1e293b] rounded px-2 py-1.5 text-sm text-white"
            @change="(e) => updateStyle('textAlign', ($event.target as HTMLSelectElement).value)">
            <option value="left">左对齐</option>
            <option value="center">居中</option>
            <option value="right">右对齐</option>
          </select>
        </div>
      </div>

      <div v-if="component.type === 'clock'" class="space-y-2">
        <h4 class="text-xs text-[#8892a0]">时间设置</h4>
        <div class="flex flex-col gap-2">
          <label class="flex items-center gap-2 text-xs text-[#8892a0]">
            <input
              type="checkbox"
              :checked="component.props?.showDate ?? true"
              @change="(e) => updateProp('showDate', (e.target as HTMLInputElement).checked)"
              class="accent-[#00d9ff]"
            />
            显示日期
          </label>
          <label class="flex items-center gap-2 text-xs text-[#8892a0]">
            <input
              type="checkbox"
              :checked="component.props?.showWeek ?? true"
              @change="(e) => updateProp('showWeek', (e.target as HTMLInputElement).checked)"
              class="accent-[#00d9ff]"
            />
            显示星期
          </label>
          <label class="flex items-center gap-2 text-xs text-[#8892a0]">
            <input
              type="checkbox"
              :checked="component.props?.showTime ?? true"
              @change="(e) => updateProp('showTime', (e.target as HTMLInputElement).checked)"
              class="accent-[#00d9ff]"
            />
            显示时间
          </label>
        </div>
        <div class="mt-2">
          <label class="text-xs text-[#8892a0]">字体大小</label>
          <input
            type="number"
            :value="component.props?.fontSize || 16"
            min="12"
            max="48"
            class="w-full bg-[#112240] border border-[#1e293b] rounded px-2 py-1 text-sm text-white"
            @input="(e) => updateProp('fontSize', Number((e.target as HTMLInputElement).value))"
          />
        </div>
        <div class="mt-2">
          <label class="text-xs text-[#8892a0]">字体颜色</label>
          <input type="color" :value="component.styles?.color || '#ffffff'"
            class="w-full h-8 bg-[#112240] border border-[#1e293b] rounded"
            @input="(e) => updateStyle('color', ($event.target as HTMLInputElement).value)" />
        </div>
        <div class="mt-2">
          <label class="text-xs text-[#8892a0]">字体粗细</label>
          <select :value="component.styles?.fontWeight || 'normal'"
            class="w-full bg-[#112240] border border-[#1e293b] rounded px-2 py-1.5 text-sm text-white"
            @change="(e) => updateStyle('fontWeight', ($event.target as HTMLSelectElement).value)">
            <option value="normal">常规</option>
            <option value="bold">加粗</option>
            <option value="lighter">细体</option>
          </select>
        </div>
        <div class="mt-2">
          <label class="text-xs text-[#8892a0]">文字对齐</label>
          <select :value="component.styles?.textAlign || 'center'"
            class="w-full bg-[#112240] border border-[#1e293b] rounded px-2 py-1.5 text-sm text-white"
            @change="(e) => updateStyle('textAlign', ($event.target as HTMLSelectElement).value)">
            <option value="left">左对齐</option>
            <option value="center">居中</option>
            <option value="right">右对齐</option>
          </select>
        </div>
      </div>

      <!-- 数据源绑定 -->
      <div v-if="['metric-card', 'counter', 'video', 'chart-line', 'chart-bar'].includes(component.type)" class="space-y-2">
        <h4 class="text-xs text-[#8892a0]">数据绑定</h4>

        <!-- 指标选择 -->
        <div v-if="component.type === 'metric-card' || component.type === 'counter'">
          <label class="text-xs text-[#8892a0]">指标</label>
          <select
            :value="component.dataSource?.key || ''"
            class="w-full bg-[#112240] border border-[#1e293b] rounded px-2 py-1.5 text-sm text-white"
            @change="(e) => updateDataSource('type', 'metric') || updateDataSource('key', (e.target as HTMLSelectElement).value)"
          >
            <option value="">请选择</option>
            <option v-for="m in METRIC_OPTIONS" :key="m.key" :value="m.key">{{ m.label }}</option>
          </select>
        </div>

        <!-- 图表数据源 -->
        <div v-else-if="component.type === 'chart-line' || component.type === 'chart-bar'">
          <label class="text-xs text-[#8892a0]">数据类型</label>
          <select
            :value="component.dataSource?.type || 'hourly'"
            class="w-full bg-[#112240] border border-[#1e293b] rounded px-2 py-1.5 text-sm text-white"
            @change="(e) => updateDataSource('type', (e.target as HTMLSelectElement).value)"
          >
            <option value="hourly">今日客流趋势</option>
          </select>
          <p class="text-xs text-[#00d9ff] mt-1">图表将自动显示今日客流数据</p>
        </div>

        <!-- 设备选择 -->
        <div v-else-if="component.type === 'video'">
          <label class="text-xs text-[#8892a0]">选择设备</label>
          <select
            :value="component.dataSource?.key || ''"
            class="w-full bg-[#112240] border border-[#1e293b] rounded px-2 py-1.5 text-sm text-white"
            @change="(e) => handleDeviceSelect((e.target as HTMLSelectElement).value)"
          >
            <option value="">请选择设备</option>
            <option v-for="d in devices" :key="d.id" :value="d.id">
              {{ d.name }} ({{ d.status === 'online' ? '在线' : '离线' }})
            </option>
          </select>
          <p v-if="devices.length === 0" class="text-xs text-[#8892a0] mt-1">
            暂无设备，请先在设备管理中添加
          </p>
          <p v-else-if="selectedDeviceName" class="text-xs text-[#00d9ff] mt-1">
            当前: {{ selectedDeviceName }}
          </p>
        </div>
      </div>

      <!-- 样式 -->
      <div class="space-y-2">
        <h4 class="text-xs text-[#8892a0]">样式</h4>
        <div>
          <label class="text-xs text-[#8892a0]">背景色</label>
          <input
            type="color"
            :value="component.styles?.backgroundColor || '#1e3a5f'"
            class="w-full h-8 bg-[#112240] border border-[#1e293b] rounded"
            @input="(e) => updateStyle('backgroundColor', (e.target as HTMLInputElement).value)"
          />
        </div>
        <div class="mt-2">
          <label class="text-xs text-[#8892a0]">边框颜色</label>
          <input
            type="color"
            :value="component.styles?.borderColor || '#1e293b'"
            class="w-full h-8 bg-[#112240] border border-[#1e293b] rounded"
            @input="(e) => updateStyle('borderColor', (e.target as HTMLInputElement).value)"
          />
        </div>
        <div class="mt-2">
          <label class="text-xs text-[#8892a0]">透明度</label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            :value="component.opacity"
            class="w-full accent-[#00d9ff]"
            @input="(e) => updatePosition('opacity', Number((e.target as HTMLInputElement).value))"
          />
        </div>
      </div>
    </div>
  </div>
</template>