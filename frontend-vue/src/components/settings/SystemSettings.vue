<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ImageIcon, Loader2, Save, Upload } from 'lucide-vue-next'
import { message } from 'ant-design-vue'

const metricOptions = [
  { key: 'todayIn', label: '今日进' },
  { key: 'todayOut', label: '今日出' },
  { key: 'currentIn', label: '当前在场' },
  { key: 'weekIn', label: '本周进' },
  { key: 'monthIn', label: '本月进' },
  { key: 'weekOut', label: '本周出' },
  { key: 'monthOut', label: '本月出' },
  { key: 'totalIn', label: '累计进' },
  { key: 'totalOut', label: '累计出' },
]

const MAX_METRICS = 4

const settings = ref({
  storeName: '我的门店',
  storeLogo: '',
  loginPassword: '',
  dashboardMetrics: ['todayIn', 'todayOut', 'currentIn', 'weekIn'],
})

const metricLabels = ref<Record<string, string>>({})

function getMetricLabel(key: string): string {
  if (metricLabels.value[key]) return metricLabels.value[key]
  const opt = metricOptions.find(o => o.key === key)
  return opt ? opt.label : key
}

const loading = ref(true)
const saving = ref(false)
const newPassword = ref('')
const fileInputRef = ref<HTMLInputElement>()

async function fetchSettings() {
  try {
    const res = await fetch('/api/settings')
    if (res.ok) {
      const json = await res.json()
      const data = json.data || json
      if (data.storeName) settings.value.storeName = data.storeName
      if (data.storeLogo) settings.value.storeLogo = data.storeLogo
      if (data.loginPassword) settings.value.loginPassword = data.loginPassword
      if (data.dashboardMetrics) {
        settings.value.dashboardMetrics = data.dashboardMetrics.split(',').filter(Boolean)
      }
      if (data.dashboardMetricsLabels) {
        try {
          metricLabels.value = JSON.parse(data.dashboardMetricsLabels)
        } catch {
          metricLabels.value = {}
        }
      }
    }
  } catch {
    message.error('加载设置失败')
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
    settings.value.storeLogo = e.target?.result as string
  }
  reader.readAsDataURL(file)
}

function handleMetricToggle(key: string) {
  const metrics = settings.value.dashboardMetrics
  const index = metrics.indexOf(key)
  if (index > -1) {
    metrics.splice(index, 1)
  } else if (metrics.length < MAX_METRICS) {
    metrics.push(key)
  } else {
    message.error(`最多选择 ${MAX_METRICS} 个指标`)
  }
}

async function handleSave() {
  saving.value = true
  try {
    const body: Record<string, string> = {
      storeName: settings.value.storeName,
      storeLogo: settings.value.storeLogo,
      dashboardMetrics: settings.value.dashboardMetrics.join(','),
      dashboardMetricsLabels: JSON.stringify(metricLabels.value),
    }
    if (newPassword.value) {
      body.loginPassword = newPassword.value
    }

    const res = await fetch('/api/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    if (res.ok) {
      if (newPassword.value) {
        settings.value.loginPassword = newPassword.value
        newPassword.value = ''
        localStorage.removeItem('fluxavision_auth_token')
        window.location.reload()
        return
      }
      message.success('设置已保存')
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

onMounted(() => {
  fetchSettings()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h2 class="text-2xl font-bold text-white">系统设置 <span class="text-sm font-normal text-[#8892a0] ml-2">管理系统基本配置和仪表盘显示</span></h2>
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading" class="space-y-6">
      <div class="bg-[#112240] border border-[#1e293b] rounded-xl p-6 space-y-4">
        <div class="h-6 w-40 bg-[#1e293b] rounded animate-pulse" />
        <div class="h-10 w-full bg-[#1e293b] rounded animate-pulse" />
      </div>
      <div class="bg-[#112240] border border-[#1e293b] rounded-xl p-6 space-y-4">
        <div class="h-6 w-40 bg-[#1e293b] rounded animate-pulse" />
        <div class="h-10 w-full bg-[#1e293b] rounded animate-pulse" />
      </div>
      <div class="bg-[#112240] border border-[#1e293b] rounded-xl p-6 space-y-4">
        <div class="h-6 w-40 bg-[#1e293b] rounded animate-pulse" />
        <div class="grid grid-cols-2 gap-4">
          <div v-for="i in 4" :key="i" class="h-20 bg-[#1e293b] rounded animate-pulse" />
        </div>
      </div>
    </div>

    <!-- Settings content -->
    <div v-else class="space-y-6">
      <!-- Store Info -->
      <div class="bg-[#112240] border border-[#1e293b] rounded-xl p-6 space-y-4">
        <h3 class="text-lg font-medium text-white">门店信息</h3>

        <div class="flex items-center gap-4">
          <label class="text-sm text-[#8892a0] w-20 flex-shrink-0 text-right">门店名称</label>
          <input
            v-model="settings.storeName"
            type="text"
            class="flex-1 bg-[#0a192f] border border-[#1e293b] rounded-md px-3 py-2 text-sm text-white outline-none focus:border-[#00d9ff] transition-colors"
            placeholder="请输入门店名称"
          />
        </div>

        <div class="flex items-center gap-4">
          <label class="text-sm text-[#8892a0] w-20 flex-shrink-0 text-right">门店Logo</label>
          <div class="flex items-center gap-3 flex-1">
            <div
              class="w-10 h-10 rounded-lg bg-[#0a192f] border border-[#1e293b] flex items-center justify-center overflow-hidden"
            >
              <img
                v-if="settings.storeLogo"
                :src="settings.storeLogo"
                alt="Logo"
                class="w-full h-full object-cover"
              />
              <ImageIcon v-else class="w-5 h-5 text-[#8892a0]" />
            </div>
            <button
              class="flex items-center gap-2 px-3 py-2 bg-[#0a192f] border border-[#1e293b] rounded-md text-sm text-[#8892a0] hover:text-white hover:border-[#00d9ff]/50 transition-colors cursor-pointer"
              @click="fileInputRef?.click()"
            >
              <Upload class="w-4 h-4" />
              上传Logo
            </button>
            <input
              ref="fileInputRef"
              type="file"
              accept="image/*"
              class="hidden"
              @change="handleFileUpload"
            />
          </div>
        </div>
      </div>

      <!-- Password -->
      <div class="bg-[#112240] border border-[#1e293b] rounded-xl p-6 space-y-4">
        <h3 class="text-lg font-medium text-white">登录密码</h3>
        <div class="flex items-start gap-4">
          <label class="text-sm text-[#8892a0] w-20 flex-shrink-0 text-right mt-2">新密码</label>
          <div class="flex-1">
            <input
              v-model="newPassword"
              type="password"
              class="w-full bg-[#0a192f] border border-[#1e293b] rounded-md px-3 py-2 text-sm text-white outline-none focus:border-[#00d9ff] transition-colors"
              placeholder="留空则不修改密码"
            />
            <p class="text-xs text-[#8892a0]/60 mt-1">修改后下次登录需要使用新密码</p>
          </div>
        </div>
      </div>

      <!-- Dashboard Metrics -->
      <div class="bg-[#112240] border border-[#1e293b] rounded-xl p-6 space-y-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <h3 class="text-lg font-medium text-white">数据指标</h3>
            <span class="text-sm text-[#8892a0]">选择要在仪表盘上显示的客流指标（最多 {{ MAX_METRICS }} 个），已选 {{ settings.dashboardMetrics.length }}/{{ MAX_METRICS }}</span>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
          <div
            v-for="opt in metricOptions"
            :key="opt.key"
            class="flex items-center gap-3 p-3 rounded-lg border transition-colors cursor-pointer"
            :class="[
              settings.dashboardMetrics.includes(opt.key)
                ? 'border-[#00d9ff]/30 bg-[#00d9ff]/5'
                : 'border-[#1e293b] bg-[#0a192f] hover:border-[#00d9ff]/20'
            ]"
            @click="handleMetricToggle(opt.key)"
          >
            <input
              type="checkbox"
              :checked="settings.dashboardMetrics.includes(opt.key)"
              :disabled="!settings.dashboardMetrics.includes(opt.key) && settings.dashboardMetrics.length >= MAX_METRICS"
              @change="handleMetricToggle(opt.key)"
              class="w-4 h-4 rounded border-[#2d4765] accent-[#00d9ff]"
            />
            <span class="text-sm" :class="settings.dashboardMetrics.includes(opt.key) ? 'text-[#00d9ff]' : 'text-[#8892a0]'">
              {{ opt.label }}
            </span>
          </div>
        </div>

      </div>

      <!-- 自定义指标名称 -->
      <div class="bg-[#112240] border border-[#1e293b] rounded-xl p-6 space-y-4">
        <h3 class="text-lg font-medium text-white">自定义指标名称</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          <div
            v-for="opt in metricOptions"
            :key="opt.key"
            class="flex items-center gap-3"
          >
            <label class="text-sm text-[#8892a0] w-20 flex-shrink-0 text-right">{{ opt.label }}</label>
            <input
              :value="metricLabels[opt.key] || ''"
              type="text"
              class="flex-1 bg-[#0a192f] border border-[#1e293b] rounded-md px-3 py-1.5 text-sm text-white outline-none focus:border-[#00d9ff] transition-colors"
              :placeholder="opt.label"
              @input="metricLabels[opt.key] = ($event.target as HTMLInputElement).value"
            />
          </div>
        </div>
      </div>
      <div class="flex justify-center pt-4">
        <button
          :disabled="saving"
          class="flex items-center gap-2 px-4 py-2 bg-[#00d9ff] text-[#0a192f] rounded-md text-sm font-medium hover:bg-[#00d9ff]/80 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-colors"
          @click="handleSave"
        >
          <Loader2 v-if="saving" class="w-4 h-4 animate-spin" />
          <Save v-else class="w-4 h-4" />
          保存设置
        </button>
      </div>
    </div>
  </div>
</template>
