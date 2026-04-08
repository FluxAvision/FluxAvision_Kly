<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, h } from 'vue'
import {
  Plus,
  Search,
  Edit2,
  Trash2,
  Wifi,
  WifiOff,
  AlertTriangle,
  Loader2,
  Eye,
  Radio,
  RefreshCw,
  XCircle,
} from 'lucide-vue-next'
import { message } from 'ant-design-vue'
import { generateRtspUrl } from '@/lib/utils'
import RTSPVideoPlayer from '@/components/video/RTSPVideoPlayer.vue'

interface Device {
  id: string
  name: string
  ip: string
  serialNumber: string
  location: string
  model: string
  rtspPort: number
  sdkPort: number
  channel: number
  username: string
  password: string
  rtspUrl: string
  status: string
  collectorState?: string
  collectorStarted?: boolean
  collectorMessage?: string
}

interface SearchDevice {
  name: string
  ip: string
  model: string
  serialNumber: string
}

const emptyDevice = {
  name: '',
  ip: '',
  serialNumber: '',
  location: '',
  model: '大华',
  rtspPort: 554,
  sdkPort: 37777,
  channel: 0,
  username: 'admin',
  password: 'admin123',
  rtspUrl: '',
  status: 'offline',
}

// State
const devices = ref<Device[]>([])
const loading = ref(true)
const searchQuery = ref('')
const dialogs = reactive({
  add: false,
  edit: false,
  search: false,
  deleteConfirm: false,
  preview: false,
})
const previewDevice = ref<Device | null>(null)
const formData = ref({ ...emptyDevice })
const editingId = ref<string | null>(null)
const deletingId = ref<string | null>(null)
const saving = ref(false)
const saveMessage = ref('')
const searchIpRange = ref('')
const searchingDevices = ref(false)
const searchResults = ref<SearchDevice[]>([])
const formErrors = ref<Record<string, string>>({})

let pollTimer: ReturnType<typeof setInterval> | null = null

// Table columns
const columns = [
  { title: '设备名称', dataIndex: 'name', key: 'name' },
  { title: '设备序列号', dataIndex: 'serialNumber', key: 'serialNumber' },
  { title: 'IP', dataIndex: 'ip', key: 'ip' },
  { title: '安装位置', dataIndex: 'location', key: 'location' },
  { title: '型号', dataIndex: 'model', key: 'model' },
  { title: '状态', key: 'status' },
  { title: '采集', key: 'collector' },
  { title: '操作', key: 'action', align: 'right' as const },
]

// Filtered devices
const filteredDevices = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return devices.value.filter(
    (d) =>
      d.name.toLowerCase().includes(q) ||
      d.ip.includes(searchQuery.value) ||
      d.location.toLowerCase().includes(q)
  )
})

// Fetch devices
async function fetchDevices() {
  try {
    const res = await fetch('/api/devices')
    if (res.ok) {
      const json = await res.json()
      const devicesData = json.data || json
      devices.value = Array.isArray(devicesData) ? devicesData : []
    }
  } catch {
    // Keep empty
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDevices()
  pollTimer = setInterval(fetchDevices, 10000)
})

onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
})

// Form helpers
function updateForm(field: string, value: string | number) {
  const updated = { ...formData.value, [field]: value }
  if (['model', 'ip', 'rtspPort', 'username', 'password'].includes(field)) {
    updated.rtspUrl = generateRtspUrl(
      updated.model,
      updated.ip,
      updated.rtspPort,
      updated.username,
      updated.password
    )
  }
  formData.value = updated
}

function resetForm() {
  formData.value = { ...emptyDevice }
  formErrors.value = {}
}

function validateForm(): boolean {
  const errors: Record<string, string> = {}
  if (!formData.value.name.trim()) errors.name = '请输入设备名称'
  if (!formData.value.serialNumber.trim()) errors.serialNumber = '请输入设备序列号'
  if (!formData.value.ip.trim()) errors.ip = '请输入IP地址'
  else if (!/^\d{1,3}(\.\d{1,3}){3}$/.test(formData.value.ip.trim())) errors.ip = 'IP地址格式不正确'
  if (!formData.value.model) errors.model = '请选择型号'
  if (formData.value.model === '大华') {
    if (!formData.value.sdkPort || formData.value.sdkPort <= 0) errors.sdkPort = '请输入SDK端口'
    if (formData.value.channel < 0) errors.channel = '请输入有效的通道号'
  }
  formErrors.value = errors
  return Object.keys(errors).length === 0
}

// Save (add or edit)
async function handleSave() {
  if (!validateForm()) return
  saving.value = true
  saveMessage.value = ''
  try {
    if (editingId.value) {
      const res = await fetch(`/api/devices/${editingId.value}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData.value),
      })
      if (res.ok) {
        dialogs.edit = false
        fetchDevices()
        message.success('保存成功', { description: `设备"${formData.value.name}"已更新。` })
      } else {
        const json = await res.json().catch(() => null)
        message.error('保存失败', { description: json?.message || '设备更新失败，请稍后重试。' })
      }
    } else {
      const res = await fetch('/api/devices', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData.value),
      })
      if (res.ok) {
        const json = await res.json()
        const msg = json.data?.collectorMessage || ''
        saveMessage.value = msg
        message.success('添加成功', { description: msg || `设备"${formData.value.name}"已添加。` })
        setTimeout(() => {
          dialogs.add = false
          saveMessage.value = ''
          fetchDevices()
        }, 2000)
      } else {
        const json = await res.json().catch(() => null)
        message.error('添加失败', { description: json?.message || '设备添加失败，请检查参数后重试。' })
      }
    }
  } catch {
    message.error(editingId.value ? '保存失败' : '添加失败', {
      description: '请求提交失败，请检查网络或后端服务。',
    })
  } finally {
    saving.value = false
  }
}

// Delete
async function handleDelete() {
  if (!deletingId.value) return
  try {
    const res = await fetch(`/api/devices/${deletingId.value}`, { method: 'DELETE' })
    if (res.ok) {
      dialogs.deleteConfirm = false
      deletingId.value = null
      fetchDevices()
      message.success('删除成功', { description: '设备已删除。' })
    } else {
      const json = await res.json().catch(() => null)
      message.error('删除失败', { description: json?.message || '设备删除失败，请稍后重试。' })
    }
  } catch {
    message.error('删除失败', { description: '删除请求未完成，请检查网络或后端服务。' })
  }
}

// Search devices on LAN
async function handleSearchDevices() {
  if (!searchIpRange.value) return
  searchingDevices.value = true
  searchResults.value = []
  await new Promise((resolve) => setTimeout(resolve, 1500))
  const baseIp = searchIpRange.value.split('.')[0]
  searchResults.value = [
    {
      name: '摄像头-001',
      ip: `${baseIp}.101`,
      model: '大华',
      serialNumber: `DH-${Date.now()}`,
    },
    {
      name: '摄像头-002',
      ip: `${baseIp}.102`,
      model: '海康威视',
      serialNumber: `HK-${Date.now()}`,
    },
  ]
  searchingDevices.value = false
}

function handleSelectSearchedDevice(device: SearchDevice) {
  formData.value = {
    ...emptyDevice,
    name: device.name,
    ip: device.ip,
    model: device.model,
    serialNumber: device.serialNumber,
    rtspUrl: generateRtspUrl(device.model, device.ip, 554, 'admin', ''),
  }
  dialogs.search = false
  dialogs.add = true
}

// Status helpers
function statusVariant(status: string): string {
  if (status === 'online') return 'bg-[#00ff88]/10 text-[#00ff88] border-[#00ff88]/20'
  if (status === 'warning') return 'bg-[#ff9500]/10 text-[#ff9500] border-[#ff9500]/20'
  return 'bg-[#ef4444]/10 text-[#ef4444] border-[#ef4444]/20'
}

function statusText(status: string): string {
  if (status === 'online') return '在线'
  if (status === 'warning') return '告警'
  return '离线'
}

// Collector state badge config
const collectorStateConfigs: Record<string, { text: string; color: string; bgColor: string; borderColor: string }> = {
  connected: { text: '采集中', color: '#00ff88', bgColor: 'rgba(0, 255, 136, 0.1)', borderColor: 'rgba(0, 255, 136, 0.2)' },
  connecting: { text: '连接中', color: '#00d9ff', bgColor: 'rgba(0, 217, 255, 0.1)', borderColor: 'rgba(0, 217, 255, 0.2)' },
  reconnecting: { text: '重连中', color: '#ff9500', bgColor: 'rgba(255, 149, 0, 0.1)', borderColor: 'rgba(255, 149, 0, 0.2)' },
  disconnected: { text: '已断线', color: '#ef4444', bgColor: 'rgba(239, 68, 68, 0.1)', borderColor: 'rgba(239, 68, 68, 0.2)' },
  stopped: { text: '已停止', color: '#8892a0', bgColor: 'rgba(136, 146, 160, 0.1)', borderColor: 'rgba(136, 146, 160, 0.2)' },
}

function getCollectorConfig(state?: string) {
  if (!state || state === 'not_started') return null
  return collectorStateConfigs[state] || null
}

// Dialog open helpers
function openAddDialog() {
  resetForm()
  editingId.value = null
  saveMessage.value = ''
  dialogs.add = true
}

function openEditDialog(device: Device) {
  formData.value = { ...device }
  editingId.value = device.id
  saveMessage.value = ''
  formErrors.value = {}
  dialogs.edit = true
}

function openDeleteConfirm(deviceId: string) {
  deletingId.value = deviceId
  dialogs.deleteConfirm = true
}

function openPreview(device: Device) {
  previewDevice.value = device
  dialogs.preview = true
}

function closePreview() {
  dialogs.preview = false
  previewDevice.value = null
}

function openSearchDialog() {
  searchIpRange.value = ''
  searchResults.value = []
  dialogs.search = true
}

function closeAddDialog() {
  dialogs.add = false
  saveMessage.value = ''
}

function closeEditDialog() {
  dialogs.edit = false
  saveMessage.value = ''
}
</script>

<template>
  <div class="space-y-4">
    <!-- Toolbar -->
    <div class="flex items-center gap-3 flex-wrap">
      <div class="relative flex-1 min-w-[200px] max-w-md">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8892a0]" />
        <input
          v-model="searchQuery"
          placeholder="搜索设备名称、IP..."
          class="w-full pl-9 pr-3 py-2 text-sm bg-[#0a192f] border border-[#1e293b] rounded-md text-white placeholder-[#8892a0]/50 outline-none focus:border-[#00d9ff] transition-colors"
        />
      </div>
      <a-button
        @click="openSearchDialog"
        class="!border-[#1e293b] !text-[#8892a0] hover:!text-white hover:!bg-[#172a45]"
      >
        <Search class="w-4 h-4 inline-block align-text-bottom mr-1" />
        搜索设备
      </a-button>
      <a-button
        @click="openAddDialog"
        class="!bg-[#00d9ff] !border-[#00d9ff] !text-[#0a192f] hover:!bg-[#00d9ff]/80 hover:!border-[#00d9ff]/80"
      >
        <Plus class="w-4 h-4 inline-block align-text-bottom mr-1" />
        添加设备
      </a-button>
    </div>

    <!-- Device Table -->
    <div class="bg-[#112240] border border-[#1e293b] rounded-lg overflow-hidden">
      <div class="overflow-x-auto">
        <a-table
          :columns="columns"
          :data-source="filteredDevices"
          :loading="loading"
          :pagination="false"
          row-key="id"
          :row-class-name="() => 'device-row'"
        >
          <!-- Loading skeleton -->
          <template #placeholder>
            <div v-for="i in 3" :key="i" class="flex gap-4 py-3 px-4">
              <div v-for="j in 7" :key="j" class="h-5 w-20 bg-[#1e293b] rounded animate-pulse" />
            </div>
          </template>

          <!-- Empty state -->
          <template #emptyText>
            <div class="py-12 text-[#8892a0]">
              {{ devices.length === 0 ? '暂无设备，请添加设备' : '未找到匹配的设备' }}
            </div>
          </template>

          <!-- Custom cell rendering -->
          <template #bodyCell="{ column, record }">
            <!-- Name column -->
            <template v-if="column.key === 'name'">
              <span class="text-white font-medium">{{ record.name }}</span>
            </template>

            <!-- serialNumber column -->
            <template v-if="column.key === 'serialNumber'">
              <span class="text-white font-medium">{{ record.serialNumber }}</span>
            </template>

            <!-- IP column -->
            <template v-else-if="column.key === 'ip'">
              <span class="text-[#8892a0] font-mono text-sm">{{ record.ip }}</span>
            </template>

            <!-- Location column -->
            <template v-else-if="column.key === 'location'">
              <span class="text-[#8892a0]">{{ record.location }}</span>
            </template>

            <!-- Model column -->
            <template v-else-if="column.key === 'model'">
              <span class="text-[#8892a0]">{{ record.model }}</span>
            </template>

            <!-- Status column -->
            <template v-else-if="column.key === 'status'">
              <span
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs"
                :class="statusVariant(record.status)"
              >
                <Wifi v-if="record.status === 'online'" class="w-3.5 h-3.5" />
                <AlertTriangle v-else-if="record.status === 'warning'" class="w-3.5 h-3.5" />
                <WifiOff v-else class="w-3.5 h-3.5" />
                <span class="ml-0.5">{{ statusText(record.status) }}</span>
              </span>
            </template>

            <!-- Collector state column -->
            <template v-else-if="column.key === 'collector'">
              <template v-if="record.model === '大华'">
                <template v-if="getCollectorConfig(record.collectorState)">
                  <span
                    class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[10px]"
                    :style="{
                      color: getCollectorConfig(record.collectorState)!.color,
                      backgroundColor: getCollectorConfig(record.collectorState)!.bgColor,
                      borderColor: getCollectorConfig(record.collectorState)!.borderColor,
                    }"
                  >
                    <Radio v-if="record.collectorState === 'connected'" class="w-3 h-3" />
                    <Loader2 v-else-if="record.collectorState === 'connecting'" class="w-3 h-3 animate-spin" />
                    <RefreshCw v-else-if="record.collectorState === 'reconnecting'" class="w-3 h-3 animate-spin" />
                    <XCircle v-else class="w-3 h-3" />
                    <span class="ml-1">{{ getCollectorConfig(record.collectorState)!.text }}</span>
                  </span>
                </template>
                <span v-else class="text-xs text-[#8892a0]">-</span>
              </template>
              <span v-else class="text-xs text-[#8892a0]">-</span>
            </template>

            <!-- Action column -->
            <template v-else-if="column.key === 'action'">
              <div class="flex items-center justify-end gap-2">
                <button
                  v-if="record.status === 'online'"
                  class="inline-flex items-center gap-1 text-[#00d9ff] hover:text-[#00d9ff] hover:bg-[#00d9ff]/10 px-2 py-1 rounded text-sm transition-colors cursor-pointer"
                  @click="openPreview(record)"
                >
                  <Eye class="w-4 h-4" />
                  <span>预览</span>
                </button>
                <button
                  class="inline-flex items-center justify-center text-[#8892a0] hover:text-white hover:bg-[#172a45] p-1.5 rounded transition-colors cursor-pointer"
                  title="编辑"
                  @click="openEditDialog(record)"
                >
                  <Edit2 class="w-4 h-4" />
                </button>
                <button
                  class="inline-flex items-center justify-center text-[#ef4444] hover:text-[#ef4444] hover:bg-[#ef4444]/10 p-1.5 rounded transition-colors cursor-pointer"
                  title="删除"
                  @click="openDeleteConfirm(record.id)"
                >
                  <Trash2 class="w-4 h-4" />
                </button>
              </div>
            </template>
          </template>
        </a-table>
      </div>
    </div>

    <!-- Add Device Dialog -->
    <a-modal
      v-model:open="dialogs.add"
      title="添加设备"
      :footer="null"
      :width="'60%'"
      :mask-closable="false"
      class="device-dialog"
    >
      <div class="grid gap-4 py-4">
        <div class="flex items-center gap-4">
          <label class="text-[#8892a0] w-20 flex-shrink-0 text-right">名称</label>
          <div class="flex-1">
            <input
              :value="formData.name"
              @input="updateForm('name', ($event.target as HTMLInputElement).value)"
              placeholder="请输入设备名称"
              :class="['bg-[#0a192f] border text-white rounded-md px-3 py-2 text-sm outline-none w-full transition-colors', formErrors.name ? 'border-[#ef4444]' : 'border-[#1e293b] focus:border-[#00d9ff]']"
            />
            <p v-if="formErrors.name" class="text-xs text-[#ef4444] mt-1">{{ formErrors.name }}</p>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-x-4 gap-y-4">
          <div class="flex items-center gap-4">
            <label class="text-[#8892a0] w-20 flex-shrink-0 text-right">IP地址</label>
            <div class="flex-1">
              <input
                :value="formData.ip"
                @input="updateForm('ip', ($event.target as HTMLInputElement).value)"
                placeholder="192.168.1.100"
                :class="['bg-[#0a192f] border text-white rounded-md px-3 py-2 text-sm outline-none w-full font-mono transition-colors', formErrors.ip ? 'border-[#ef4444]' : 'border-[#1e293b] focus:border-[#00d9ff]']"
              />
              <p v-if="formErrors.ip" class="text-xs text-[#ef4444] mt-1">{{ formErrors.ip }}</p>
            </div>
          </div>
          <div class="flex items-center gap-4">
            <label class="text-[#8892a0] w-20 flex-shrink-0 text-right">序列号</label>
            <div class="flex-1">
              <input
                :value="formData.serialNumber"
                @input="updateForm('serialNumber', ($event.target as HTMLInputElement).value)"
                placeholder="设备序列号"
                :class="['bg-[#0a192f] border text-white rounded-md px-3 py-2 text-sm outline-none w-full transition-colors', formErrors.serialNumber ? 'border-[#ef4444]' : 'border-[#1e293b] focus:border-[#00d9ff]']"
              />
              <p v-if="formErrors.serialNumber" class="text-xs text-[#ef4444] mt-1">{{ formErrors.serialNumber }}</p>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-4">
          <label class="text-[#8892a0] w-20 flex-shrink-0 text-right">安装位置</label>
          <div class="flex-1">
            <input
              :value="formData.location"
              @input="updateForm('location', ($event.target as HTMLInputElement).value)"
              placeholder="如：一楼入口（可选）"
              class="bg-[#0a192f] border border-[#1e293b] text-white rounded-md px-3 py-2 text-sm outline-none focus:border-[#00d9ff] w-full transition-colors"
            />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-x-4 gap-y-4">
          <div class="flex items-center gap-4">
            <label class="text-[#8892a0] w-20 flex-shrink-0 text-right">型号</label>
            <div class="flex-1">
              <a-select
                :value="formData.model"
                @change="(v: string) => updateForm('model', v)"
                class="w-full"
                popup-class-name="dark-select-dropdown"
              >
                <a-select-option value="大华">大华</a-select-option>
                <a-select-option value="海康威视">海康威视</a-select-option>
                <a-select-option value="通用">通用</a-select-option>
              </a-select>
            </div>
          </div>
          <div class="flex items-center gap-4">
            <label class="text-[#8892a0] w-20 flex-shrink-0 text-right">RTSP端口</label>
            <div class="flex-1">
              <input
                type="number"
                :value="formData.rtspPort"
                @input="updateForm('rtspPort', Number(($event.target as HTMLInputElement).value))"
                placeholder="554"
                class="bg-[#0a192f] border border-[#1e293b] text-white rounded-md px-3 py-2 text-sm outline-none focus:border-[#00d9ff] w-full font-mono transition-colors"
              />
            </div>
          </div>
        </div>

        <!-- Dahua SDK specific fields -->
        <div v-if="formData.model === '大华'" class="grid grid-cols-2 gap-x-4 gap-y-4">
          <div class="flex items-start gap-4">
            <label class="text-[#8892a0] w-20 flex-shrink-0 text-right pt-2">SDK端口</label>
            <div class="flex-1">
              <input
                type="number"
                :value="formData.sdkPort"
                @input="updateForm('sdkPort', Number(($event.target as HTMLInputElement).value))"
                placeholder="37777"
                :class="['bg-[#0a192f] border text-white rounded-md px-3 py-2 text-sm outline-none w-full font-mono transition-colors', formErrors.sdkPort ? 'border-[#ef4444]' : 'border-[#1e293b] focus:border-[#00d9ff]']"
              />
              <p class="text-[10px] text-[#8892a0]/60">大华默认 37777</p>
            </div>
          </div>
          <div class="flex items-start gap-4">
            <label class="text-[#8892a0] w-20 flex-shrink-0 text-right pt-2">通道号</label>
            <div class="flex-1">
              <input
                type="number"
                :value="formData.channel"
                @input="updateForm('channel', Number(($event.target as HTMLInputElement).value))"
                placeholder="0"
                min="0"
                :class="['bg-[#0a192f] border text-white rounded-md px-3 py-2 text-sm outline-none w-full font-mono transition-colors', formErrors.channel ? 'border-[#ef4444]' : 'border-[#1e293b] focus:border-[#00d9ff]']"
              />
              <p class="text-[10px] text-[#8892a0]/60">从0开始, 通常是0</p>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-x-4 gap-y-4">
          <div class="flex items-center gap-4">
            <label class="text-[#8892a0] w-20 flex-shrink-0 text-right">用户名</label>
            <div class="flex-1">
              <input
                :value="formData.username"
                @input="updateForm('username', ($event.target as HTMLInputElement).value)"
                class="bg-[#0a192f] border border-[#1e293b] text-white rounded-md px-3 py-2 text-sm outline-none focus:border-[#00d9ff] w-full transition-colors"
              />
            </div>
          </div>
          <div class="flex items-center gap-4">
            <label class="text-[#8892a0] w-20 flex-shrink-0 text-right">密码</label>
            <div class="flex-1">
              <input
                type="password"
                :value="formData.password"
                @input="updateForm('password', ($event.target as HTMLInputElement).value)"
                class="bg-[#0a192f] border border-[#1e293b] text-white rounded-md px-3 py-2 text-sm outline-none focus:border-[#00d9ff] w-full transition-colors"
              />
            </div>
          </div>
        </div>
        <div class="flex items-center gap-4">
          <label class="text-[#8892a0] w-20 flex-shrink-0 text-right">RTSP地址</label>
          <div class="flex-1">
            <input
              :value="formData.rtspUrl"
              @input="updateForm('rtspUrl', ($event.target as HTMLInputElement).value)"
              placeholder="自动生成"
              class="bg-[#0a192f] border border-[#1e293b] text-white rounded-md px-3 py-2 text-xs outline-none focus:border-[#00d9ff] w-full font-mono transition-colors"
            />
          </div>
        </div>
        <div v-if="saveMessage" class="text-xs text-[#00ff88] bg-[#00ff88]/5 border border-[#00ff88]/20 rounded-md p-2">
          {{ saveMessage }}
        </div>
      </div>
      <div class="flex justify-end gap-2 mt-4 pt-4 border-t border-[#1e293b]">
        <button
          @click="closeAddDialog"
          class="px-4 py-2 text-sm text-[#8892a0] hover:text-white transition-colors cursor-pointer"
        >
          取消
        </button>
        <button
          @click="handleSave"
          :disabled="saving"
          class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md bg-[#00d9ff] text-[#0a192f] hover:bg-[#00d9ff]/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer"
        >
          <Loader2 v-if="saving" class="w-4 h-4 animate-spin" />
          添加
        </button>
      </div>
    </a-modal>

    <!-- Edit Device Dialog -->
    <a-modal
      v-model:open="dialogs.edit"
      title="编辑设备"
      :footer="null"
      :width="'60%'"
      :mask-closable="false"
      class="device-dialog"
    >
      <div class="grid gap-4 py-4">
        <div class="flex items-center gap-4">
          <label class="text-[#8892a0] w-20 flex-shrink-0 text-right">名称</label>
          <div class="flex-1">
            <input
              :value="formData.name"
              @input="updateForm('name', ($event.target as HTMLInputElement).value)"
              :class="['bg-[#0a192f] border text-white rounded-md px-3 py-2 text-sm outline-none w-full transition-colors', formErrors.name ? 'border-[#ef4444]' : 'border-[#1e293b] focus:border-[#00d9ff]']"
            />
            <p v-if="formErrors.name" class="text-xs text-[#ef4444] mt-1">{{ formErrors.name }}</p>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-x-4 gap-y-4">
          <div class="flex items-center gap-4">
            <label class="text-[#8892a0] w-20 flex-shrink-0 text-right">IP地址</label>
            <div class="flex-1">
              <input
                :value="formData.ip"
                @input="updateForm('ip', ($event.target as HTMLInputElement).value)"
                :class="['bg-[#0a192f] border text-white rounded-md px-3 py-2 text-sm outline-none w-full font-mono transition-colors', formErrors.ip ? 'border-[#ef4444]' : 'border-[#1e293b] focus:border-[#00d9ff]']"
              />
              <p v-if="formErrors.ip" class="text-xs text-[#ef4444] mt-1">{{ formErrors.ip }}</p>
            </div>
          </div>
          <div class="flex items-center gap-4">
            <label class="text-[#8892a0] w-20 flex-shrink-0 text-right">序列号</label>
            <div class="flex-1">
              <input
                :value="formData.serialNumber"
                @input="updateForm('serialNumber', ($event.target as HTMLInputElement).value)"
                :class="['bg-[#0a192f] border text-white rounded-md px-3 py-2 text-sm outline-none w-full transition-colors', formErrors.serialNumber ? 'border-[#ef4444]' : 'border-[#1e293b] focus:border-[#00d9ff]']"
              />
              <p v-if="formErrors.serialNumber" class="text-xs text-[#ef4444] mt-1">{{ formErrors.serialNumber }}</p>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-4">
          <label class="text-[#8892a0] w-20 flex-shrink-0 text-right">安装位置</label>
          <div class="flex-1">
            <input
              :value="formData.location"
              @input="updateForm('location', ($event.target as HTMLInputElement).value)"
              placeholder="如：一楼入口（可选）"
              class="bg-[#0a192f] border border-[#1e293b] text-white rounded-md px-3 py-2 text-sm outline-none focus:border-[#00d9ff] w-full transition-colors"
            />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-x-4 gap-y-4">
          <div class="flex items-center gap-4">
            <label class="text-[#8892a0] w-20 flex-shrink-0 text-right">型号</label>
            <div class="flex-1">
              <a-select
                :value="formData.model"
                @change="(v: string) => updateForm('model', v)"
                class="w-full"
                popup-class-name="dark-select-dropdown"
              >
                <a-select-option value="大华">大华</a-select-option>
                <a-select-option value="海康威视">海康威视</a-select-option>
                <a-select-option value="通用">通用</a-select-option>
              </a-select>
            </div>
          </div>
          <div class="flex items-center gap-4">
            <label class="text-[#8892a0] w-20 flex-shrink-0 text-right">RTSP端口</label>
            <div class="flex-1">
              <input
                type="number"
                :value="formData.rtspPort"
                @input="updateForm('rtspPort', Number(($event.target as HTMLInputElement).value))"
                class="bg-[#0a192f] border border-[#1e293b] text-white rounded-md px-3 py-2 text-sm outline-none focus:border-[#00d9ff] w-full font-mono transition-colors"
              />
            </div>
          </div>
        </div>

        <!-- Dahua SDK specific fields -->
        <div v-if="formData.model === '大华'" class="grid grid-cols-2 gap-x-4 gap-y-4">
          <div class="flex items-start gap-4">
            <label class="text-[#8892a0] w-20 flex-shrink-0 text-right pt-2">SDK端口</label>
            <div class="flex-1">
              <input
                type="number"
                :value="formData.sdkPort"
                @input="updateForm('sdkPort', Number(($event.target as HTMLInputElement).value))"
                :class="['bg-[#0a192f] border text-white rounded-md px-3 py-2 text-sm outline-none w-full font-mono transition-colors', formErrors.sdkPort ? 'border-[#ef4444]' : 'border-[#1e293b] focus:border-[#00d9ff]']"
              />
              <p class="text-[10px] text-[#8892a0]/60">大华默认 37777</p>
            </div>
          </div>
          <div class="flex items-start gap-4">
            <label class="text-[#8892a0] w-20 flex-shrink-0 text-right pt-2">通道号</label>
            <div class="flex-1">
              <input
                type="number"
                :value="formData.channel"
                @input="updateForm('channel', Number(($event.target as HTMLInputElement).value))"
                min="0"
                :class="['bg-[#0a192f] border text-white rounded-md px-3 py-2 text-sm outline-none w-full font-mono transition-colors', formErrors.channel ? 'border-[#ef4444]' : 'border-[#1e293b] focus:border-[#00d9ff]']"
              />
              <p class="text-[10px] text-[#8892a0]/60">从0开始, 通常是0</p>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-x-4 gap-y-4">
          <div class="flex items-center gap-4">
            <label class="text-[#8892a0] w-20 flex-shrink-0 text-right">用户名</label>
            <div class="flex-1">
              <input
                :value="formData.username"
                @input="updateForm('username', ($event.target as HTMLInputElement).value)"
                class="bg-[#0a192f] border border-[#1e293b] text-white rounded-md px-3 py-2 text-sm outline-none focus:border-[#00d9ff] w-full transition-colors"
              />
            </div>
          </div>
          <div class="flex items-center gap-4">
            <label class="text-[#8892a0] w-20 flex-shrink-0 text-right">密码</label>
            <div class="flex-1">
              <input
                type="password"
                :value="formData.password"
                @input="updateForm('password', ($event.target as HTMLInputElement).value)"
                class="bg-[#0a192f] border border-[#1e293b] text-white rounded-md px-3 py-2 text-sm outline-none focus:border-[#00d9ff] w-full transition-colors"
              />
            </div>
          </div>
        </div>
        <div class="flex items-center gap-4">
          <label class="text-[#8892a0] w-20 flex-shrink-0 text-right">RTSP地址</label>
          <div class="flex-1">
            <input
              :value="formData.rtspUrl"
              @input="updateForm('rtspUrl', ($event.target as HTMLInputElement).value)"
              class="bg-[#0a192f] border border-[#1e293b] text-white rounded-md px-3 py-2 text-xs outline-none focus:border-[#00d9ff] w-full font-mono transition-colors"
            />
          </div>
        </div>
        <div v-if="saveMessage" class="text-xs text-[#00ff88] bg-[#00ff88]/5 border border-[#00ff88]/20 rounded-md p-2">
          {{ saveMessage }}
        </div>
      </div>
      <div class="flex justify-end gap-2 mt-4 pt-4 border-t border-[#1e293b]">
        <button
          @click="closeEditDialog"
          class="px-4 py-2 text-sm text-[#8892a0] hover:text-white transition-colors cursor-pointer"
        >
          取消
        </button>
        <button
          @click="handleSave"
          :disabled="saving"
          class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md bg-[#00d9ff] text-[#0a192f] hover:bg-[#00d9ff]/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer"
        >
          <Loader2 v-if="saving" class="w-4 h-4 animate-spin" />
          保存
        </button>
      </div>
    </a-modal>

    <!-- Search Device Dialog -->
    <a-modal
      v-model:open="dialogs.search"
      title="搜索局域网设备"
      :footer="null"
      :width="512"
      class="device-dialog"
    >
      <div class="space-y-4 py-4">
        <div class="grid gap-2">
          <label class="text-[#8892a0]">IP地址段</label>
          <div class="flex gap-2">
            <input
              v-model="searchIpRange"
              placeholder="192.168.1"
              class="flex-1 bg-[#0a192f] border border-[#1e293b] text-white rounded-md px-3 py-2 text-sm outline-none focus:border-[#00d9ff] font-mono transition-colors"
            />
            <button
              @click="handleSearchDevices"
              :disabled="searchingDevices"
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md bg-[#00d9ff] text-[#0a192f] hover:bg-[#00d9ff]/80 disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0 transition-colors cursor-pointer"
            >
              <Loader2 v-if="searchingDevices" class="w-4 h-4 animate-spin" />
              搜索
            </button>
          </div>
        </div>
        <div v-if="searchResults.length > 0" class="space-y-2">
          <label class="text-[#8892a0]">发现 {{ searchResults.length }} 个设备</label>
          <div class="space-y-2 max-h-60 overflow-y-auto">
            <div
              v-for="(device, i) in searchResults"
              :key="i"
              class="flex items-center justify-between bg-[#0a192f] border border-[#1e293b] rounded-lg p-3 hover:border-[#00d9ff]/30 transition-colors"
            >
              <div>
                <p class="text-sm text-white">{{ device.name }}</p>
                <p class="text-xs text-[#8892a0] font-mono">
                  {{ device.ip }} &middot; {{ device.model }}
                </p>
              </div>
              <button
                @click="handleSelectSearchedDevice(device)"
                class="px-3 py-1 text-sm font-medium rounded-md bg-[#00d9ff] text-[#0a192f] hover:bg-[#00d9ff]/80 transition-colors cursor-pointer"
              >
                选择
              </button>
            </div>
          </div>
        </div>
      </div>
    </a-modal>

    <!-- Video Preview Dialog -->
    <a-modal
      v-model:open="dialogs.preview"
      :footer="null"
      :width="1200"
      :closable="true"
      :mask-closable="true"
      :body-style="{ padding: 0, overflow: 'hidden', height: '80vh' }"
      :wrap-class-name="'preview-dialog-wrapper'"
      @cancel="closePreview"
    >
      <template #title>
        <span class="text-white">{{ previewDevice?.name || '' }}</span>
      </template>
      <div class="h-full">
        <RTSPVideoPlayer
          v-if="previewDevice"
          :device-id="previewDevice.id"
          :status="previewDevice.status"
          :auto-play="true"
          :show-controls="true"
          :compact="false"
          class="w-full h-full"
        />
      </div>
    </a-modal>

    <!-- Delete Confirm Dialog -->
    <a-modal
      v-model:open="dialogs.deleteConfirm"
      title="确认删除"
      :footer="null"
      :width="400"
      class="device-dialog"
    >
      <p class="text-[#8892a0] text-sm">
        确定要删除该设备吗？删除后将自动停止客流采集并清理相关数据，此操作不可撤销。
      </p>
      <div class="flex justify-end gap-2 mt-6 pt-4 border-t border-[#1e293b]">
        <button
          @click="dialogs.deleteConfirm = false"
          class="px-4 py-2 text-sm text-[#8892a0] hover:text-white transition-colors cursor-pointer"
        >
          取消
        </button>
        <button
          @click="handleDelete"
          class="px-4 py-2 text-sm font-medium rounded-md bg-[#ef4444] text-white hover:bg-[#ef4444]/80 transition-colors cursor-pointer"
        >
          删除
        </button>
      </div>
    </a-modal>
  </div>
</template>

<style scoped>
:deep(.device-dialog .ant-modal-content) {
  background-color: #112240;
  border: 1px solid #1e293b;
  max-height: 85vh;
  overflow-y: auto;
}

:deep(.device-dialog .ant-modal-header) {
  background-color: #112240;
  border-bottom: 1px solid #1e293b;
}

:deep(.device-dialog .ant-modal-title) {
  color: #ffffff;
}

:deep(.device-dialog .ant-modal-close) {
  color: #8892a0;
}

:deep(.device-dialog .ant-modal-close:hover) {
  color: #ffffff;
}

:deep(.device-dialog .ant-select-selector) {
  background-color: #0a192f !important;
  border-color: #1e293b !important;
  color: #ffffff !important;
}

:deep(.device-dialog .ant-select-selection-item) {
  color: #ffffff !important;
}

:deep(.device-dialog .ant-select-arrow) {
  color: #8892a0 !important;
}

:deep(.device-dialog .ant-select-selection-placeholder) {
  color: #8892a0 !important;
}

/* Table dark theme overrides */
:deep(.ant-table) {
  background-color: transparent !important;
}

:deep(.ant-table-thead > tr > th) {
  background-color: #0a192f !important;
  color: #8892a0 !important;
  border-bottom-color: #1e293b !important;
  font-weight: 500;
}

:deep(.ant-table-tbody > tr > td) {
  border-bottom-color: #1e293b !important;
  background-color: transparent !important;
}

:deep(.ant-table-tbody > tr:hover > td) {
  background-color: rgba(23, 42, 69, 0.5) !important;
}

:deep(.ant-table-placeholder) {
  background-color: transparent !important;
}

:deep(.ant-table-placeholder .ant-table-cell) {
  background-color: transparent !important;
}

:deep(.ant-empty-description) {
  color: #8892a0 !important;
}

:deep(.ant-spin-dot-item) {
  background-color: #00d9ff !important;
}

/* Preview dialog overrides */
:deep(.preview-dialog-wrapper .ant-modal-content) {
  background-color: #112240;
  border: 1px solid #1e293b;
  height: 86vh;
  max-height: 900px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

:deep(.preview-dialog-wrapper .ant-modal-header) {
  background-color: #142544;
  border-bottom: 1px solid #1e293b;
  flex-shrink: 0;
}

:deep(.preview-dialog-wrapper .ant-modal-body) {
  padding: 0;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

:deep(.preview-dialog-wrapper .ant-modal-title) {
  color: #ffffff;
}

:deep(.preview-dialog-wrapper .ant-modal-close) {
  color: #8892a0;
}

:deep(.preview-dialog-wrapper .ant-modal-close:hover) {
  color: #ffffff;
}
</style>
