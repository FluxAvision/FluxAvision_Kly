<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Key, Copy, Check, Loader2 } from 'lucide-vue-next'
import { message } from 'ant-design-vue'

interface LicenseData {
  hardwareFingerprint: string
  isActive: boolean
  isExpired: boolean
  expiryDate: string
  maxDevices: number
  remainingDays: number
}

const license = ref<LicenseData>({
  hardwareFingerprint: '',
  isActive: false,
  isExpired: false,
  expiryDate: '',
  maxDevices: 4,
  remainingDays: 0,
})
const activating = ref(false)
const activationCode = ref('')
const copied = ref(false)
const loading = ref(true)

async function fetchLicense() {
  loading.value = true
  try {
    const res = await fetch('/api/license')
    if (res.ok) {
      const json = await res.json()
      const data = json.data || json
      license.value = {
        hardwareFingerprint: data.hardwareFingerprint || '',
        isActive: data.isActive || false,
        isExpired: data.isExpired || false,
        expiryDate: data.expiryDate || '',
        maxDevices: data.maxDevices || 4,
        remainingDays: data.remainingDays || 0,
      }
    }
  } catch {
    message.error('加载License信息失败')
  } finally {
    loading.value = false
  }
}

async function handleActivate() {
  if (!activationCode.value.trim()) {
    message.error('请输入激活码')
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
        isExpired: data.isExpired || false,
        expiryDate: data.expiryDate || '',
        maxDevices: data.maxDevices || 4,
        remainingDays: data.remainingDays || 0,
      }
      activationCode.value = ''
      message.success(license.value.isActive ? '授权已更新' : '激活成功')
    } else {
      const errJson = await res.json().catch(() => ({}))
      message.error(errJson.message || '激活失败')
    }
  } catch {
    message.error('激活失败')
  } finally {
    activating.value = false
  }
}

async function handleCopyFingerprint() {
  try {
    await navigator.clipboard.writeText(license.value.hardwareFingerprint)
    copied.value = true
    message.success('硬件指纹已复制')
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    message.error('复制失败')
  }
}

const statusColor = computed(() => {
  if (!license.value.isActive || license.value.isExpired) {
    return { border: 'border-[#ff9500]/30 bg-[#ff9500]/5', bg: 'bg-[#ff9500]/20', icon: 'text-[#ff9500]', text: 'text-[#ff9500]' }
  }
  if (license.value.remainingDays < 15) {
    return { border: 'border-[#ff9500]/30 bg-[#ff9500]/5', bg: 'bg-[#ff9500]/20', icon: 'text-[#ff9500]', text: 'text-[#ff9500]' }
  }
  return { border: 'border-[#00ff88]/30 bg-[#00ff88]/5', bg: 'bg-[#00ff88]/20', icon: 'text-[#00ff88]', text: 'text-[#00ff88]' }
})

onMounted(() => {
  fetchLicense()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h2 class="text-2xl font-bold text-white">License管理 <span class="text-sm font-normal text-[#8892a0] ml-2">管理软件授权许可</span></h2>
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading" class="bg-[#112240] border border-[#1e293b] rounded-xl p-6 space-y-4">
      <div class="h-6 w-40 bg-[#1e293b] rounded animate-pulse" />
      <div class="h-10 w-full bg-[#1e293b] rounded animate-pulse" />
    </div>

    <div v-else class="space-y-6">
      <!-- License Status -->
      <div
        class="rounded-xl p-4 border"
        :class="statusColor.border"
      >
        <div class="flex items-center gap-3">
          <div
            class="w-10 h-10 rounded-full flex items-center justify-center"
            :class="statusColor.bg"
          >
            <Key class="w-5 h-5" :class="statusColor.icon" />
          </div>
          <div class="flex-1">
            <p class="text-sm font-medium" :class="statusColor.text">
              {{ license.isExpired ? '授权已过期' : license.isActive ? 'License 已激活' : 'License 未激活' }}
            </p>
            <p class="text-xs text-[#8892a0]">
              <span v-if="license.isExpired">已于 {{ license.expiryDate }} 到期，请重新激活</span>
              <span v-else-if="license.isActive">有效期至: {{ license.expiryDate }}（剩余 {{ license.remainingDays }} 天）</span>
              <span v-else>请激活License以使用全部功能</span>
            </p>
          </div>
          <div v-if="license.isActive && !license.isExpired" class="text-right">
            <p class="text-xs text-[#8892a0]">设备限额</p>
            <p class="text-lg font-bold text-white">{{ license.maxDevices }}</p>
          </div>
        </div>
      </div>

      <!-- Hardware Fingerprint -->
      <div class="bg-[#112240] border border-[#1e293b] rounded-xl p-6 space-y-4">
        <div class="flex items-center gap-4">
          <label class="text-sm text-[#8892a0] w-20 flex-shrink-0 text-right">硬件指纹</label>
          <div class="flex items-center gap-2 flex-1">
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
      </div>

      <!-- Activation -->
      <div class="bg-[#112240] border border-[#1e293b] rounded-xl p-6 space-y-4">
        <div class="flex items-center justify-between">
          <label class="text-sm text-[#8892a0] w-20 flex-shrink-0 text-right">{{ license.isActive ? '授权码' : '激活码' }}</label>
          <span v-if="license.isActive" class="text-xs text-[#8892a0]/60">输入新授权码将覆盖当前授权</span>
        </div>
        <div class="ml-24 space-y-2">
        <textarea
          v-model="activationCode"
          placeholder="请输入激活码..."
          class="w-full bg-[#0a192f] border border-[#1e293b] rounded-md px-3 py-2 text-sm text-white outline-none focus:border-[#00d9ff] min-h-[80px] font-mono text-xs resize-none transition-colors"
        />
        <div class="flex justify-center pt-2">
          <button
            :disabled="activating || !activationCode.trim()"
            class="flex items-center gap-2 px-4 py-2 bg-[#00d9ff] text-[#0a192f] rounded-md text-sm font-medium hover:bg-[#00d9ff]/80 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-colors"
            @click="handleActivate"
          >
          <Loader2 v-if="activating" class="w-4 h-4 animate-spin" />
          <Key v-else class="w-4 h-4" />
          {{ license.isActive ? '更新授权' : '激活License' }}
          </button>
        </div>
        </div>
      </div>
    </div>
  </div>
</template>
