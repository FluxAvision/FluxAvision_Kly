<script setup lang="ts">
import { ref } from 'vue'
import { Shield, KeyRound, ArrowRight, Loader2, Copy, Check } from 'lucide-vue-next'
import { message } from 'ant-design-vue'

const props = defineProps<{
  hasPassword: boolean
  isLicensed: boolean
  hardwareFingerprint: string
}>()

const emit = defineEmits<{
  login: []
  activateLicense: [code: string]
}>()

const password = ref('')
const activatingCode = ref('')
const activating = ref(false)
const error = ref('')
const copied = ref(false)

async function handleCopyFingerprint() {
  try {
    await navigator.clipboard.writeText(props.hardwareFingerprint)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // ignore
  }
}

function handleActivate() {
  if (!activatingCode.value.trim()) return
  activating.value = true
  error.value = ''
  try {
    emit('activateLicense', activatingCode.value.trim())
  } catch {
    error.value = '激活失败，请检查激活码'
  } finally {
    activating.value = false
  }
}

function handleLogin() {
  if (props.hasPassword && !password.value) {
    error.value = '请输入密码'
    return
  }
  error.value = ''
  emit('login')
}

function handleKeyDown(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    if (!props.isLicensed) {
      handleActivate()
    } else {
      handleLogin()
    }
  }
}
</script>

<template>
  <div class="min-h-screen bg-[#0a192f] flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <!-- Logo & Title -->
      <div class="text-center mb-8">
        <div class="w-16 h-16 flex items-center justify-center mx-auto mb-4">
          <img src="/logo.png" alt="FluxaVision" class="w-16 h-16 rounded-2xl" />
        </div>
        <h1 class="text-2xl font-bold text-white mb-2">FluxaVision客流统计系统</h1>
        <p class="text-sm text-[#8892a0]">智能客流分析与管理平台</p>
      </div>

      <!-- Card -->
      <div class="bg-[#112240] border border-[#1e293b] rounded-xl p-8">
        <!-- License Activation -->
        <div v-if="!isLicensed" class="space-y-6">
          <div class="flex items-center gap-3">
            <Shield class="w-5 h-5 text-[#ff9500]" />
            <h2 class="text-lg font-medium text-white">系统激活</h2>
          </div>
          <p class="text-sm text-[#8892a0]">请先激活系统License以使用全部功能</p>

          <div class="grid gap-2">
            <label class="text-[#8892a0] text-xs">硬件指纹</label>
            <div class="flex items-center gap-2">
              <div class="flex-1 bg-[#0a192f] border border-[#1e293b] rounded-lg px-3 py-2 font-mono text-xs text-[#8892a0] break-all">
                {{ hardwareFingerprint || '正在生成...' }}
              </div>
              <button
                :disabled="!hardwareFingerprint || copied"
                class="flex items-center gap-1 px-2 py-2 bg-[#0a192f] border border-[#1e293b] rounded-lg text-xs text-[#8892a0] hover:text-white hover:border-[#00d9ff]/50 disabled:opacity-50 transition-colors cursor-pointer flex-shrink-0"
                @click="handleCopyFingerprint"
              >
                <Check v-if="copied" class="w-3.5 h-3.5 text-[#00ff88]" />
                <Copy v-else class="w-3.5 h-3.5" />
                {{ copied ? '已复制' : '复制' }}
              </button>
            </div>
          </div>

          <div class="grid gap-2">
            <label class="text-[#8892a0] text-xs">激活码</label>
            <textarea
              v-model="activatingCode"
              @keydown="handleKeyDown"
              placeholder="请输入激活码..."
              class="bg-[#0a192f] border-[#1e293b] min-h-[100px] font-mono text-xs resize-none text-[#ffffff] rounded-md px-3 py-2 outline-none focus:border-[#00d9ff]"
            />
          </div>

          <p v-if="error" class="text-sm text-[#ef4444]">{{ error }}</p>

          <button
            :disabled="activating || !activatingCode.trim()"
            class="w-full bg-[#00d9ff] text-[#0a192f] hover:bg-[#00d9ff]/80 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 px-4 py-2 rounded-md text-sm font-medium cursor-pointer transition-colors"
            @click="handleActivate"
          >
            <Loader2 v-if="activating" class="w-4 h-4 animate-spin" />
            <Shield v-else class="w-4 h-4" />
            激活系统
          </button>
        </div>

        <!-- Password Login -->
        <div v-else-if="hasPassword" class="space-y-6">
          <div class="flex items-center gap-3">
            <KeyRound class="w-5 h-5 text-[#00d9ff]" />
            <h2 class="text-lg font-medium text-white">登录系统</h2>
          </div>

          <div class="grid gap-2">
            <label class="text-[#8892a0]">登录密码</label>
            <input
              v-model="password"
              type="password"
              @keydown="handleKeyDown"
              @input="error = ''"
              placeholder="请输入登录密码"
              autofocus
              class="bg-[#0a192f] border border-[#1e293b] text-white rounded-md px-3 py-2 text-sm outline-none focus:border-[#00d9ff]"
            />
          </div>

          <p v-if="error" class="text-sm text-[#ef4444]">{{ error }}</p>

          <button
            class="w-full bg-[#00d9ff] text-[#0a192f] hover:bg-[#00d9ff]/80 flex items-center justify-center gap-2 px-4 py-2 rounded-md text-sm font-medium cursor-pointer transition-colors"
            @click="handleLogin"
          >
            <span>进入系统</span>
            <ArrowRight class="w-4 h-4" />
          </button>
        </div>

        <!-- No Password - Direct Entry -->
        <div v-else class="space-y-6 text-center">
          <div class="flex items-center justify-center gap-3 mb-2">
            <Shield class="w-5 h-5 text-[#00ff88]" />
            <h2 class="text-lg font-medium text-white">系统已就绪</h2>
          </div>
          <p class="text-sm text-[#8892a0]">系统未设置登录密码，点击下方按钮进入</p>

          <button
            class="w-full bg-[#00d9ff] text-[#0a192f] hover:bg-[#00d9ff]/80 flex items-center justify-center gap-2 px-4 py-2 rounded-md text-sm font-medium cursor-pointer transition-colors"
            @click="handleLogin"
          >
            <span>进入系统</span>
            <ArrowRight class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- Footer -->
      <p class="text-center text-xs text-[#8892a0]/50 mt-6">
        FluxaVision v2.1.0 · 客流统计系统
      </p>
    </div>
  </div>
</template>
