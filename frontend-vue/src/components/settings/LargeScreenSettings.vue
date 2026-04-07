<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ImageIcon, Loader2, Save, Upload, Copy, Check, Key, Monitor } from 'lucide-vue-next'
import { toast } from 'vue-sonner'

interface Device {
  id: string
  name: string
  status: string
  location?: string
}

interface LicenseData {
  hardwareFingerprint: string
  isActive: boolean
  expiryDate: string
  maxDevices: number
}

interface LargeScreenConfig {
  title: string
  subtitle: string
  logo: string
  backgroundImage: string
  metrics: string[]
  deviceIds: string[]
  templateId: string
}

const DEFAULT_CONFIG: LargeScreenConfig = {
  title: '客流统计大屏',
  subtitle: '实时客流数据展示',
  logo: '',
  backgroundImage: '',
  metrics: ['todayIn', 'todayOut', 'currentIn'],
  deviceIds: [],
  templateId: '',
}

const MAX_SCREEN_METRICS = 4
const MAX_SCREEN_DEVICES = 4

const templates = [
  { id: 'tpl-blue', name: '科技蓝', color: '#00d9ff', desc: '深色背景配青色科技感风格' },
  { id: 'tpl-tech', name: '科技绿', color: '#00ff88', desc: '深色背景配绿色科技感风格' },
  { id: 'tpl-minimal', name: '简约白', color: '#ffffff', desc: '浅色背景配简约现代风格' },
  { id: 'tpl-data', name: '数据风', color: '#a78bfa', desc: '深色背景配紫色数据可视化风格' },
]

const metricOptions = [
  { key: 'todayIn', label: '今日进' },
  { key: 'todayOut', label: '今日出' },
  { key: 'currentIn', label: '当前在场' },
  { key: 'weekIn', label: '本周进' },
  { key: 'weekOut', label: '本周出' },
  { key: 'monthIn', label: '本月进' },
  { key: 'monthOut', label: '本月出' },
  { key: 'totalIn', label: '累计进' },
  { key: 'totalOut', label: '累计出' },
]

const activeTab = ref('general')
const config = ref<LargeScreenConfig>({ ...DEFAULT_CONFIG })
const license = ref<LicenseData>({
  hardwareFingerprint: '',
  isActive: false,
  expiryDate: '',
  maxDevices: 4,
})
const devices = ref<Device[]>([])
const loading = ref(true)
const saving = ref(false)
const activating = ref(false)
const activationCode = ref('')
const copied = ref(false)
const logoInputRef = ref<HTMLInputElement>()
const bgInputRef = ref<HTMLInputElement>()

async function fetchAll() {
  loading.value = true
  try {
    const [screenRes, devicesRes, licenseRes] = await Promise.all([
      fetch('/api/large-screen'),
      fetch('/api/devices'),
      fetch('/api/license'),
    ])

    if (screenRes.ok) {
      const json = await screenRes.json()
      const data = json.data || json
      config.value = {
        title: data.title || DEFAULT_CONFIG.title,
        subtitle: data.subtitle || DEFAULT_CONFIG.subtitle,
        logo: data.logo || '',
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

    if (licenseRes.ok) {
      const json = await licenseRes.json()
      const data = json.data || json
      license.value = {
        hardwareFingerprint: data.hardwareFingerprint || '',
        isActive: data.isActive || false,
        expiryDate: data.expiryDate || '',
        maxDevices: data.maxDevices || 4,
      }
    }
  } catch {
    toast.error('加载大屏配置失败')
  } finally {
    loading.value = false
  }
}

function handleFileUpload(type: 'logo' | 'background') {
  return (event: Event) => {
    const target = event.target as HTMLInputElement
    const file = target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      const result = e.target?.result as string
      if (type === 'logo') {
        config.value.logo = result
      } else {
        config.value.backgroundImage = result
      }
    }
    reader.readAsDataURL(file)
  }
}

function handleDeviceToggle(deviceId: string) {
  const ids = config.value.deviceIds
  const index = ids.indexOf(deviceId)
  if (index > -1) {
    ids.splice(index, 1)
  } else if (ids.length < MAX_SCREEN_DEVICES) {
    ids.push(deviceId)
  } else {
    toast.error(`最多选择 ${MAX_SCREEN_DEVICES} 个设备`)
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
    toast.error(`最多选择 ${MAX_SCREEN_METRICS} 个指标`)
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
        logo: config.value.logo,
        backgroundImage: config.value.backgroundImage,
        metrics: config.value.metrics.join(','),
        deviceIds: config.value.deviceIds.join(','),
        templateId: config.value.templateId,
      }),
    })

    if (res.ok) {
      toast.success('大屏配置已保存')
    } else {
      toast.error('保存失败')
    }
  } catch {
    toast.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleTemplateSelect(templateId: string) {
  config.value.templateId = templateId
  try {
    await fetch('/api/large-screen', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...config.value,
        metrics: config.value.metrics.join(','),
        deviceIds: config.value.deviceIds.join(','),
        templateId,
      }),
    })
    toast.success('模板已切换')
  } catch {
    toast.error('模板切换失败')
  }
}

async function handleActivate() {
  if (!activationCode.value.trim()) {
    toast.error('请输入激活码')
    return
  }
  activating.value = true
  try {
    const res = await fetch('/api/license', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ activationCode: activationCode.value.trim() }),
    })

    if (res.ok) {
      const json = await res.json()
      const data = json.data || json
      license.value = {
        hardwareFingerprint: data.hardwareFingerprint || license.value.hardwareFingerprint,
        isActive: data.isActive || false,
        expiryDate: data.expiryDate || '',
        maxDevices: data.maxDevices || 4,
      }
      activationCode.value = ''
      toast.success('激活成功')
    } else {
      const errJson = await res.json().catch(() => ({}))
      toast.error(errJson.message || '激活失败')
    }
  } catch {
    toast.error('激活失败')
  } finally {
    activating.value = false
  }
}

async function handleCopyFingerprint() {
  try {
    await navigator.clipboard.writeText(license.value.hardwareFingerprint)
    copied.value = true
    toast.success('硬件指纹已复制')
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch {
    toast.error('复制失败')
  }
}

onMounted(() => {
  fetchAll()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-white">大屏设置</h2>
        <p class="text-[#8892a0] mt-1">配置大屏显示内容和样式</p>
      </div>
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
            <!-- Title & Subtitle -->
            <div class="space-y-2">
              <label class="text-sm text-[#8892a0]">大屏标题</label>
              <input
                v-model="config.title"
                type="text"
                class="w-full bg-[#0a192f] border border-[#1e293b] rounded-md px-3 py-2 text-sm text-white outline-none focus:border-[#00d9ff] transition-colors"
                placeholder="请输入大屏标题"
              />
            </div>

            <div class="space-y-2">
              <label class="text-sm text-[#8892a0]">副标题</label>
              <input
                v-model="config.subtitle"
                type="text"
                class="w-full bg-[#0a192f] border border-[#1e293b] rounded-md px-3 py-2 text-sm text-white outline-none focus:border-[#00d9ff] transition-colors"
                placeholder="请输入副标题"
              />
            </div>

            <!-- Logo -->
            <div class="space-y-2">
              <label class="text-sm text-[#8892a0]">大屏Logo</label>
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-[#0a192f] border border-[#1e293b] flex items-center justify-center overflow-hidden">
                  <img v-if="config.logo" :src="config.logo" alt="Logo" class="w-full h-full object-cover" />
                  <ImageIcon v-else class="w-5 h-5 text-[#8892a0]" />
                </div>
                <button
                  class="flex items-center gap-2 px-3 py-2 bg-[#0a192f] border border-[#1e293b] rounded-md text-sm text-[#8892a0] hover:text-white hover:border-[#00d9ff]/50 transition-colors cursor-pointer"
                  @click="logoInputRef?.click()"
                >
                  <Upload class="w-4 h-4" />
                  上传Logo
                </button>
                <input
                  ref="logoInputRef"
                  type="file"
                  accept="image/*"
                  class="hidden"
                  @change="handleFileUpload('logo')"
                />
              </div>
            </div>

            <!-- Background Image -->
            <div class="space-y-2">
              <label class="text-sm text-[#8892a0]">背景图片</label>
              <div class="flex items-center gap-3">
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
                  @change="handleFileUpload('background')"
                />
              </div>
            </div>

            <!-- Metrics Selection -->
            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <label class="text-sm text-[#8892a0]">显示指标</label>
                <span class="text-xs text-[#8892a0]">已选 {{ config.metrics.length }}/{{ MAX_SCREEN_METRICS }}</span>
              </div>
              <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
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
                <label class="text-sm text-[#8892a0]">显示设备</label>
                <span class="text-xs text-[#8892a0]">已选 {{ config.deviceIds.length }}/{{ MAX_SCREEN_DEVICES }}</span>
              </div>
              <div v-if="devices.length === 0" class="text-sm text-[#8892a0] py-4 text-center">
                暂无在线设备
              </div>
              <div v-else class="grid grid-cols-2 md:grid-cols-4 gap-2">
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
            <p class="text-sm text-[#8892a0]">选择大屏显示模板</p>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div
                v-for="tpl in templates"
                :key="tpl.id"
                class="rounded-xl border-2 p-4 cursor-pointer transition-all duration-200 hover:scale-[1.02]"
                :class="[
                  config.templateId === tpl.id
                    ? 'border-[#00d9ff] bg-[#00d9ff]/5'
                    : 'border-[#1e293b] bg-[#0a192f] hover:border-[#00d9ff]/30'
                ]"
                @click="handleTemplateSelect(tpl.id)"
              >
                <div
                  class="w-full h-24 rounded-lg mb-3 flex items-center justify-center"
                  :style="{ background: `linear-gradient(135deg, ${tpl.color}20, ${tpl.color}05)` }"
                >
                  <Monitor class="w-8 h-8" :style="{ color: tpl.color }" />
                </div>
                <h4 class="text-sm font-medium text-white">{{ tpl.name }}</h4>
                <p class="text-xs text-[#8892a0] mt-1">{{ tpl.desc }}</p>
                <div v-if="config.templateId === tpl.id" class="mt-2">
                  <span class="text-xs text-[#00d9ff]">当前使用</span>
                </div>
              </div>
            </div>
          </div>
        </a-tab-pane>

        <!-- License Tab -->
        <a-tab-pane key="license" tab="License管理">
          <div class="pb-6 space-y-6">
            <!-- License Status -->
            <div
              class="rounded-xl p-4 border"
              :class="license.isActive ? 'border-[#00ff88]/30 bg-[#00ff88]/5' : 'border-[#ff9500]/30 bg-[#ff9500]/5'"
            >
              <div class="flex items-center gap-3">
                <div
                  class="w-10 h-10 rounded-full flex items-center justify-center"
                  :class="license.isActive ? 'bg-[#00ff88]/20' : 'bg-[#ff9500]/20'"
                >
                  <Key class="w-5 h-5" :class="license.isActive ? 'text-[#00ff88]' : 'text-[#ff9500]'" />
                </div>
                <div>
                  <p class="text-sm font-medium" :class="license.isActive ? 'text-[#00ff88]' : 'text-[#ff9500]'">
                    {{ license.isActive ? 'License 已激活' : 'License 未激活' }}
                  </p>
                  <p class="text-xs text-[#8892a0]">
                    <span v-if="license.isActive">有效期至: {{ license.expiryDate }}</span>
                    <span v-else>请激活License以使用大屏功能</span>
                  </p>
                </div>
              </div>
            </div>

            <!-- Hardware Fingerprint -->
            <div class="space-y-2">
              <label class="text-sm text-[#8892a0]">硬件指纹</label>
              <div class="flex items-center gap-2">
                <div class="flex-1 bg-[#0a192f] border border-[#1e293b] rounded-md px-3 py-2 font-mono text-xs text-[#8892a0] break-all">
                  {{ license.hardwareFingerprint || '正在生成...' }}
                </div>
                <button
                  :disabled="!license.hardwareFingerprint"
                  class="flex items-center gap-1 px-3 py-2 bg-[#0a192f] border border-[#1e293b] rounded-md text-sm text-[#8892a0] hover:text-white hover:border-[#00d9ff]/50 disabled:opacity-50 transition-colors cursor-pointer"
                  @click="handleCopyFingerprint"
                >
                  <Check v-if="copied" class="w-4 h-4 text-[#00ff88]" />
                  <Copy v-else class="w-4 h-4" />
                  {{ copied ? '已复制' : '复制' }}
                </button>
              </div>
            </div>

            <!-- Activation -->
            <div v-if="!license.isActive" class="space-y-2">
              <label class="text-sm text-[#8892a0]">激活码</label>
              <textarea
                v-model="activationCode"
                placeholder="请输入激活码..."
                class="w-full bg-[#0a192f] border border-[#1e293b] rounded-md px-3 py-2 text-sm text-white outline-none focus:border-[#00d9ff] min-h-[80px] font-mono text-xs resize-none transition-colors"
              />
              <button
                :disabled="activating || !activationCode.trim()"
                class="flex items-center gap-2 px-4 py-2 bg-[#00d9ff] text-[#0a192f] rounded-md text-sm font-medium hover:bg-[#00d9ff]/80 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-colors"
                @click="handleActivate"
              >
                <Loader2 v-if="activating" class="w-4 h-4 animate-spin" />
                <Key v-else class="w-4 h-4" />
                激活License
              </button>
            </div>

            <!-- Device Limit Info -->
            <div class="space-y-2">
              <label class="text-sm text-[#8892a0]">设备限额</label>
              <div class="bg-[#0a192f] border border-[#1e293b] rounded-md px-3 py-2 text-sm text-white">
                最多支持 {{ license.maxDevices }} 个设备
              </div>
            </div>
          </div>
        </a-tab-pane>
      </a-tabs>
    </div>
  </div>
</template>
