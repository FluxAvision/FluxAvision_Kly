<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Loader2, Save, Upload, Monitor, Plus, Edit, Copy, Trash2, Eye } from 'lucide-vue-next'
import { message } from 'ant-design-vue'
import TemplateEditor from '@/components/template-editor/TemplateEditor.vue'
import type { TemplateConfig, ScreenTemplateData } from '@/types/template-editor'
import { parseTemplateConfig } from '@/types/template-editor'

interface Device {
  id: string
  name: string
  status: string
  location?: string
}

interface LargeScreenConfig {
  title: string
  subtitle: string
  backgroundImage: string
  metrics: string[]
  deviceIds: string[]
  templateId: string
}

interface Template {
  id: string
  name: string
  description: string
  thumbnail: string
  layout: string
  templateConfig: string | TemplateConfig
  canvasWidth: number
  canvasHeight: number
  backgroundColor: string
  backgroundImage: string
  isSystem: boolean
  isPublished: boolean
  createdAt: string
  updatedAt: string
}

const DEFAULT_CONFIG: LargeScreenConfig = {
  title: '客流统计大屏',
  subtitle: '实时客流数据展示',
  backgroundImage: '',
  metrics: ['todayIn', 'todayOut', 'currentIn'],
  deviceIds: [],
  templateId: '',
}

const MAX_SCREEN_METRICS = 8
const MAX_SCREEN_DEVICES = 8

// 内置模板
const builtinTemplates = [
  { id: 'tpl-general', name: '通用模板', color: '#4a9eff', desc: '居中层级布局，大数字计数器 + 分栏指标卡片', isBuiltin: true },
  { id: 'tpl-minimal', name: '简约模板', color: '#3b82f6', desc: '网格结构布局，中心面板 + 四角指标面板', isBuiltin: true },
  { id: 'tpl-standard', name: '标准模板', color: '#ef4444', desc: '欢迎大字标题 + 累计来访数字翻牌 + 当日、本月、全年统计', isBuiltin: true },
]

const metricOptions = [
  { key: 'todayIn', label: '今日进' },
  { key: 'todayOut', label: '今日出' },
  { key: 'currentIn', label: '当前在场' },
  { key: 'weekIn', label: '本周进' },
  { key: 'weekOut', label: '本周出' },
  { key: 'monthIn', label: '本月进' },
  { key: 'monthOut', label: '本月出' },
  { key: 'yearIn', label: '本年进' },
  { key: 'yearOut', label: '本年出' },
  { key: 'totalIn', label: '累计进' },
  { key: 'totalOut', label: '累计出' },
  { key: 'instantaneousMaxCapacity', label: '瞬时可承载人数' },
  { key: 'storeMaxCapacity', label: '最大可承载人数' },
  { key: 'availableCapacity', label: '可接待人数' },
]

const activeTab = ref('general')
const config = ref<LargeScreenConfig>({ ...DEFAULT_CONFIG })
const devices = ref<Device[]>([])
const templates = ref<Template[]>([])
const loading = ref(true)
const saving = ref(false)
const bgInputRef = ref<HTMLInputElement>()

// 编辑器状态
const showEditor = ref(false)
const editingTemplateId = ref<string | null>(null)
const editingTemplateName = ref<string>('')
const editingTemplateConfig = ref<TemplateConfig | string | null>(null)

// 合并后的模板列表
const allTemplates = computed(() => {
  const customTemplates = templates.value.map(t => ({ ...t, isBuiltin: false }))
  return [...builtinTemplates, ...customTemplates]
})

async function fetchAll() {
  loading.value = true
  try {
    const [screenRes, devicesRes, templatesRes] = await Promise.all([
      fetch('/api/large-screen'),
      fetch('/api/devices'),
      fetch('/api/large-screen/templates'),
    ])

    if (screenRes.ok) {
      const json = await screenRes.json()
      const data = json.data || json
      config.value = {
        title: data.title || DEFAULT_CONFIG.title,
        subtitle: data.subtitle || DEFAULT_CONFIG.subtitle,
        backgroundImage: data.backgroundImage || '',
        metrics: data.metrics ? data.metrics.split(',').filter(Boolean) : [...DEFAULT_CONFIG.metrics],
        deviceIds: data.deviceIds ? data.deviceIds.split(',').filter(Boolean) : [],
        templateId: data.templateId || '',
      }
    }

    if (devicesRes.ok) {
      const json = await devicesRes.json()
      const data = json.data || json
      devices.value = Array.isArray(data) ? data : []
    }

    if (templatesRes.ok) {
      const json = await templatesRes.json()
      templates.value = json.data || []
    }
  } catch {
    message.error('加载大屏配置失败')
  } finally {
    loading.value = false
  }
}

function handleFileUpload(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (e) => {
    config.value.backgroundImage = e.target?.result as string
  }
  reader.readAsDataURL(file)
}

function handleDeviceToggle(deviceId: string) {
  const ids = config.value.deviceIds
  const index = ids.indexOf(deviceId)
  if (index > -1) {
    ids.splice(index, 1)
  } else if (ids.length < MAX_SCREEN_DEVICES) {
    ids.push(deviceId)
  } else {
    message.error(`最多选择 ${MAX_SCREEN_DEVICES} 个设备`)
  }
}

function handleMetricToggle(key: string) {
  const metrics = config.value.metrics
  const index = metrics.indexOf(key)
  if (index > -1) {
    metrics.splice(index, 1)
  } else if (metrics.length < MAX_SCREEN_METRICS) {
    metrics.push(key)
  } else {
    message.error(`最多选择 ${MAX_SCREEN_METRICS} 个指标`)
  }
}

async function handleSave() {
  saving.value = true
  try {
    const res = await fetch('/api/large-screen', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: config.value.title,
        subtitle: config.value.subtitle,
        backgroundImage: config.value.backgroundImage,
        metrics: config.value.metrics.join(','),
        deviceIds: config.value.deviceIds.join(','),
        templateId: config.value.templateId,
      }),
    })

    if (res.ok) {
      message.success('大屏配置已保存')
    } else {
      const errData = await res.json().catch(() => ({}))
      message.error(`保存失败: ${errData.message || res.statusText}`)
    }
  } catch (e: any) {
    message.error(`保存失败: ${e.message || '网络错误'}`)
  } finally {
    saving.value = false
  }
}

async function handleTemplateSelect(templateId: string) {
  config.value.templateId = templateId
  try {
    const res = await fetch('/api/large-screen', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...config.value,
        metrics: config.value.metrics.join(','),
        deviceIds: config.value.deviceIds.join(','),
        templateId,
      }),
    })
    if (res.ok) {
      message.success('模板已切换')
    } else {
      config.value.templateId = templateId === config.value.templateId ? '' : config.value.templateId
      const errData = await res.json().catch(() => ({}))
      message.error(`模板切换失败: ${errData.message || res.statusText}`)
    }
  } catch (e: any) {
    message.error(`模板切换失败: ${e.message || '网络错误'}`)
  }
}

// 新建模板
function handleCreateTemplate() {
  editingTemplateId.value = null
  editingTemplateName.value = ''
  editingTemplateConfig.value = null
  showEditor.value = true
}

// 编辑模板
function handleEditTemplate(template: Template) {
  if ((template as any).isBuiltin) {
    message.error('内置模板不可编辑')
    return
  }
  editingTemplateId.value = template.id
  editingTemplateName.value = template.name
  editingTemplateConfig.value = template.templateConfig
  showEditor.value = true
}

// 复制模板
async function handleDuplicateTemplate(template: Template) {
  try {
    const res = await fetch(`/api/large-screen/templates/${template.id}/duplicate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: `${template.name} (副本)` }),
    })
    if (res.ok) {
      message.success('模板已复制')
      fetchAll()
    } else {
      const errData = await res.json().catch(() => ({}))
      message.error(`复制失败: ${errData.message || '未知错误'}`)
    }
  } catch (e: any) {
    message.error(`复制失败: ${e.message || '网络错误'}`)
  }
}

// 删除模板
async function handleDeleteTemplate(template: Template) {
  if (!confirm(`确定删除模板「${template.name}」吗？`)) return

  try {
    const res = await fetch(`/api/large-screen/templates/${template.id}`, {
      method: 'DELETE',
    })
    if (res.ok) {
      message.success('模板已删除')
      // 如果删除的是当前使用的模板，清除选择
      if (config.value.templateId === template.id) {
        config.value.templateId = ''
      }
      fetchAll()
    } else {
      const errData = await res.json().catch(() => ({}))
      message.error(`删除失败: ${errData.message || '未知错误'}`)
    }
  } catch (e: any) {
    message.error(`删除失败: ${e.message || '网络错误'}`)
  }
}

// 编辑器保存完成
function handleEditorSaved(template: any) {
  showEditor.value = false
  fetchAll()
  // 自动选中新创建的模板
  if (template && template.id) {
    config.value.templateId = template.id
  }
}

// 编辑器返回
function handleEditorBack() {
  showEditor.value = false
}

// 处理模板重命名
function handleEditorRenamed(name: string) {
  editingTemplateName.value = name
}

onMounted(() => {
  fetchAll()
})
</script>

<template>
  <!-- 模板编辑器全屏模式 -->
  <TemplateEditor
    v-if="showEditor"
    :template-id="editingTemplateId || undefined"
    :template-name="editingTemplateName"
    :initial-config="editingTemplateConfig"
    @saved="handleEditorSaved"
    @back="handleEditorBack"
    @renamed="handleEditorRenamed"
  />

  <!-- 设置页面 -->
  <div v-else class="space-y-6">
    <!-- Header -->
    <div>
      <h2 class="text-2xl font-bold text-white">大屏设置 <span class="text-sm font-normal text-[#8892a0] ml-2">配置大屏显示内容和样式</span></h2>
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading" class="space-y-6">
      <div class="bg-[#112240] border border-[#1e293b] rounded-xl p-6 space-y-4">
        <div class="h-6 w-40 bg-[#1e293b] rounded animate-pulse" />
        <div class="h-10 w-full bg-[#1e293b] rounded animate-pulse" />
        <div class="h-10 w-full bg-[#1e293b] rounded animate-pulse" />
      </div>
      <div class="bg-[#112240] border border-[#1e293b] rounded-xl p-6 space-y-4">
        <div class="h-6 w-40 bg-[#1e293b] rounded animate-pulse" />
        <div class="grid grid-cols-2 gap-4">
          <div v-for="i in 4" :key="i" class="h-28 bg-[#1e293b] rounded animate-pulse" />
        </div>
      </div>
    </div>

    <!-- Tabs content -->
    <div v-else class="bg-[#112240] border border-[#1e293b] rounded-xl">
      <a-tabs v-model:activeKey="activeTab" class="px-6 pt-4">
        <!-- General Tab -->
        <a-tab-pane key="general" tab="通用配置">
          <div class="space-y-6 pb-6">
            <!-- Title -->
            <div class="flex items-center gap-4">
              <label class="text-sm text-[#8892a0] w-20 flex-shrink-0 text-right">大屏标题</label>
              <input
                v-model="config.title"
                type="text"
                class="flex-1 bg-[#0a192f] border border-[#1e293b] rounded-md px-3 py-2 text-sm text-white outline-none focus:border-[#00d9ff] transition-colors"
                placeholder="请输入大屏标题"
              />
            </div>

            <!-- Subtitle -->
            <div class="flex items-center gap-4">
              <label class="text-sm text-[#8892a0] w-20 flex-shrink-0 text-right">副标题</label>
              <input
                v-model="config.subtitle"
                type="text"
                class="flex-1 bg-[#0a192f] border border-[#1e293b] rounded-md px-3 py-2 text-sm text-white outline-none focus:border-[#00d9ff] transition-colors"
                placeholder="请输入副标题"
              />
            </div>


            <!-- Background Image -->
            <div class="flex items-center gap-4">
              <label class="text-sm text-[#8892a0] w-20 flex-shrink-0 text-right">背景图片</label>
              <div class="flex items-center gap-3 flex-1">
                <div class="w-16 h-10 rounded-lg bg-[#0a192f] border border-[#1e293b] flex items-center justify-center overflow-hidden">
                  <img v-if="config.backgroundImage" :src="config.backgroundImage" alt="Background" class="w-full h-full object-cover" />
                  <Monitor v-else class="w-5 h-5 text-[#8892a0]" />
                </div>
                <button
                  class="flex items-center gap-2 px-3 py-2 bg-[#0a192f] border border-[#1e293b] rounded-md text-sm text-[#8892a0] hover:text-white hover:border-[#00d9ff]/50 transition-colors cursor-pointer"
                  @click="bgInputRef?.click()"
                >
                  <Upload class="w-4 h-4" />
                  上传背景
                </button>
                <button
                  v-if="config.backgroundImage"
                  class="px-3 py-2 text-sm text-[#ef4444] hover:text-[#ef4444]/80 transition-colors cursor-pointer"
                  @click="config.backgroundImage = ''"
                >
                  移除
                </button>
                <input
                  ref="bgInputRef"
                  type="file"
                  accept="image/*"
                  class="hidden"
                  @change="handleFileUpload"
                />
              </div>
            </div>

            <!-- Metrics Selection -->
            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <label class="text-sm text-[#8892a0] w-20 flex-shrink-0 text-right">显示指标</label>
                <span class="text-xs text-[#8892a0]">已选 {{ config.metrics.length }}/{{ MAX_SCREEN_METRICS }}</span>
              </div>
              <div class="grid grid-cols-2 md:grid-cols-4 gap-2 ml-24">
                <div
                  v-for="opt in metricOptions"
                  :key="opt.key"
                  class="flex items-center gap-2 p-2.5 rounded-lg border transition-colors cursor-pointer"
                  :class="[
                    config.metrics.includes(opt.key)
                      ? 'border-[#00d9ff]/30 bg-[#00d9ff]/5'
                      : 'border-[#1e293b] bg-[#0a192f] hover:border-[#00d9ff]/20'
                  ]"
                  @click="handleMetricToggle(opt.key)"
                >
                  <input
                    type="checkbox"
                    :checked="config.metrics.includes(opt.key)"
                    :disabled="!config.metrics.includes(opt.key) && config.metrics.length >= MAX_SCREEN_METRICS"
                    @change="handleMetricToggle(opt.key)"
                    class="w-4 h-4 rounded border-[#2d4765] accent-[#00d9ff]"
                  />
                  <span class="text-sm" :class="config.metrics.includes(opt.key) ? 'text-[#00d9ff]' : 'text-[#8892a0]'">
                    {{ opt.label }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Device Selection -->
            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <label class="text-sm text-[#8892a0] w-20 flex-shrink-0 text-right">显示设备</label>
                <span class="text-xs text-[#8892a0]">已选 {{ config.deviceIds.length }}/{{ MAX_SCREEN_DEVICES }}</span>
              </div>
              <div v-if="devices.length === 0" class="text-sm text-[#8892a0] py-4 text-center ml-24">
                暂无在线设备
              </div>
              <div v-else class="grid grid-cols-2 md:grid-cols-4 gap-2 ml-24">
                <div
                  v-for="device in devices"
                  :key="device.id"
                  class="flex items-center gap-2 p-2.5 rounded-lg border transition-colors cursor-pointer"
                  :class="[
                    config.deviceIds.includes(device.id)
                      ? 'border-[#00d9ff]/30 bg-[#00d9ff]/5'
                      : 'border-[#1e293b] bg-[#0a192f] hover:border-[#00d9ff]/20'
                  ]"
                  @click="handleDeviceToggle(device.id)"
                >
                  <input
                    type="checkbox"
                    :checked="config.deviceIds.includes(device.id)"
                    :disabled="!config.deviceIds.includes(device.id) && config.deviceIds.length >= MAX_SCREEN_DEVICES"
                    @change="handleDeviceToggle(device.id)"
                    class="w-4 h-4 rounded border-[#2d4765] accent-[#00d9ff]"
                  />
                  <span class="text-sm truncate" :class="config.deviceIds.includes(device.id) ? 'text-[#00d9ff]' : 'text-[#8892a0]'">
                    {{ device.name }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </a-tab-pane>

        <!-- Templates Tab -->
        <a-tab-pane key="templates" tab="大屏模板">
          <div class="pb-6 space-y-4">
            <div class="flex items-center justify-between">
              <p class="text-sm text-[#8892a0]">选择或创建大屏模板</p>
              <button
                class="flex items-center gap-2 px-3 py-1.5 bg-[#00d9ff] text-[#0a192f] rounded-md text-sm font-medium hover:bg-[#00d9ff]/80 transition-colors cursor-pointer"
                @click="handleCreateTemplate"
              >
                <Plus class="w-4 h-4" />
                新建模板
              </button>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div
                v-for="tpl in allTemplates"
                :key="tpl.id"
                class="rounded-xl border-2 p-4 cursor-pointer transition-all duration-200 hover:scale-[1.02]"
                :class="[
                  config.templateId === tpl.id
                    ? 'border-[#00d9ff] bg-[#00d9ff]/5'
                    : 'border-[#1e293b] bg-[#0a192f] hover:border-[#00d9ff]/30'
                ]"
              >
                <!-- 缩略图 -->
                <div
                  class="w-full h-24 rounded-lg mb-3 flex items-center justify-center overflow-hidden"
                  :style="{ background: `linear-gradient(135deg, ${(tpl as any).color || '#4a9eff'}20, ${(tpl as any).color || '#4a9eff'}05)` }"
                  @click="handleTemplateSelect(tpl.id)"
                >
                  <img v-if="tpl.thumbnail" :src="tpl.thumbnail" class="w-full h-full object-cover" />
                  <Monitor v-else class="w-8 h-8" :style="{ color: (tpl as any).color || '#4a9eff' }" />
                </div>

                <!-- 信息 -->
                <div class="flex items-start justify-between">
                  <div @click="handleTemplateSelect(tpl.id)">
                    <h4 class="text-sm font-medium text-white flex items-center gap-1.5">
                      {{ tpl.name }}
                      <span v-if="(tpl as any).isBuiltin" class="text-xs px-1.5 py-0.5 rounded bg-[#1e293b] text-[#8892a0]">内置</span>
                      <span v-else-if="tpl.isSystem" class="text-xs px-1.5 py-0.5 rounded bg-[#4a9eff]/20 text-[#4a9eff]">系统</span>
                    </h4>
                    <p class="text-xs text-[#8892a0] mt-1 line-clamp-2">{{ (tpl as any).desc || tpl.description || '自定义模板' }}</p>
                  </div>

                  <!-- 操作按钮 -->
                  <div v-if="!(tpl as any).isBuiltin && !tpl.isSystem" class="flex items-center gap-1">
                    <button
                      class="p-1.5 rounded hover:bg-white/10 text-[#8892a0] hover:text-white transition-colors cursor-pointer"
                      title="编辑"
                      @click.stop="handleEditTemplate(tpl)"
                    >
                      <Edit class="w-3.5 h-3.5" />
                    </button>
                    <button
                      class="p-1.5 rounded hover:bg-white/10 text-[#8892a0] hover:text-white transition-colors cursor-pointer"
                      title="复制"
                      @click.stop="handleDuplicateTemplate(tpl)"
                    >
                      <Copy class="w-3.5 h-3.5" />
                    </button>
                    <button
                      class="p-1.5 rounded hover:bg-white/10 text-[#8892a0] hover:text-[#ef4444] transition-colors cursor-pointer"
                      title="删除"
                      @click.stop="handleDeleteTemplate(tpl)"
                    >
                      <Trash2 class="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <!-- 当前使用标记 -->
                <div v-if="config.templateId === tpl.id" class="mt-2">
                  <span class="text-xs text-[#00d9ff]">当前使用</span>
                </div>
              </div>
            </div>
          </div>
        </a-tab-pane>
      </a-tabs>
      <div class="flex justify-center pt-4">
        <button
          :disabled="saving"
          class="flex items-center gap-2 px-4 py-2 bg-[#00d9ff] text-[#0a192f] rounded-md text-sm font-medium hover:bg-[#00d9ff]/80 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-colors"
          @click="handleSave"
        >
          <Loader2 v-if="saving" class="w-4 h-4 animate-spin" />
          <Save v-else class="w-4 h-4" />
          保存配置
        </button>
      </div>
    </div>
  </div>
</template>
