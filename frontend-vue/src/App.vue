<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ConfigProvider, message } from 'ant-design-vue'
import { antdTheme } from '@/lib/antd-theme'
import Sidebar from '@/components/layout/Sidebar.vue'
import Header from '@/components/layout/Header.vue'
import Dashboard from '@/components/dashboard/Dashboard.vue'
import DeviceManagement from '@/components/devices/DeviceManagement.vue'
import HistoryData from '@/components/history/HistoryData.vue'
import SystemSettings from '@/components/settings/SystemSettings.vue'
import LargeScreenList from '@/components/large-screen/LargeScreenList.vue'
import LicenseSettings from '@/components/settings/LicenseSettings.vue'
import LoginPage from '@/components/auth/LoginPage.vue'

// 配置 message
message.config({
  top: '60px',
  duration: 3,
  maxCount: 3,
})

interface LicenseData {
  isActive: boolean
  isExpired: boolean
  hardwareFingerprint: string
  expiryDate: string
  maxDevices: number
}

interface SettingsData {
  storeName: string
  loginPassword: string
  dashboardMetrics: string
  dashboardMetricsLabels: string
}

const pageTitles: Record<string, string> = {
  dashboard: '仪表盘',
  devices: '设备管理',
  history: '历史数据',
  settings: '系统设置',
  'large-screen-settings': '大屏设置',
  'license-settings': 'License管理',
}

const AUTH_TOKEN_KEY = 'fluxavision_auth_token'
const TOKEN_EXPIRY_DAYS = 30

function isAuthTokenValid(): boolean {
  try {
    const raw = localStorage.getItem(AUTH_TOKEN_KEY)
    if (!raw) return false
    const data = JSON.parse(raw)
    if (!data.ts) return false
    return (Date.now() - data.ts) < TOKEN_EXPIRY_DAYS * 24 * 60 * 60 * 1000
  } catch {
    return false
  }
}

function saveAuthToken() {
  localStorage.setItem(AUTH_TOKEN_KEY, JSON.stringify({ ts: Date.now() }))
}

function clearAuthToken() {
  localStorage.removeItem(AUTH_TOKEN_KEY)
}

const currentPage = ref('dashboard')
const isLoggedIn = ref(isAuthTokenValid())
const isLoading = ref(true)
const isLicensed = ref(false)
const hasPassword = ref(false)
const hardwareFingerprint = ref('')
const storeName = ref('我的门店')
const dashboardMetrics = ref('todayIn,todayOut,currentIn,weekIn')
const dashboardMetricsLabels = ref('')

const pageTitle = computed(() => pageTitles[currentPage.value] || '仪表盘')

async function checkSystemStatus() {
  try {
    const [licenseRes, settingsRes] = await Promise.all([
      fetch('/api/license'),
      fetch('/api/settings'),
    ])

    if (licenseRes.ok) {
      const licenseJson = await licenseRes.json()
      const license: LicenseData = licenseJson.data || licenseJson
      isLicensed.value = license.isActive && !license.isExpired
      if (license.isExpired) {
        clearAuthToken()
        isLoggedIn.value = false
      }
      hardwareFingerprint.value = license.hardwareFingerprint || ''
    }

    if (settingsRes.ok) {
      const settingsJson = await settingsRes.json()
      const settings: SettingsData = settingsJson.data || settingsJson
      storeName.value = settings.storeName || '我的门店'
      hasPassword.value = !!settings.loginPassword
      dashboardMetrics.value = settings.dashboardMetrics || 'todayIn,todayOut,currentIn,weekIn'
      dashboardMetricsLabels.value = settings.dashboardMetricsLabels || ''
    }
  } catch {
    // Keep defaults
  } finally {
    isLoading.value = false
  }
}

async function handleActivateLicense(code: string) {
  try {
    const res = await fetch('/api/license', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ activationCode: code }),
    })
    if (res.ok) {
      const json = await res.json()
      const license = json.data || json
      isLicensed.value = license.isActive && !license.isExpired
    }
  } catch {
    // Handle error
  }
}

function handleLogin() {
  isLoggedIn.value = true
  saveAuthToken()
}

function handlePageChange(page: string) {
  currentPage.value = page
}

function navigateToScreen() {
  // 在新窗口打开大屏页面
  window.open('/large-screen.html', '_blank')
}

onMounted(() => {
  checkSystemStatus()
})
</script>

<template>
  <ConfigProvider :theme="antdTheme">
    <!-- Loading state -->
    <div v-if="isLoading" class="min-h-screen bg-[#0a192f] flex items-center justify-center">
      <div class="text-center">
        <div class="w-12 h-12 rounded-xl bg-[#00d9ff]/10 flex items-center justify-center mx-auto mb-4">
          <div class="w-8 h-8 rounded-lg bg-[#1e293b] animate-pulse" />
        </div>
        <div class="h-6 w-40 mx-auto mb-2 bg-[#1e293b] rounded animate-pulse" />
        <div class="h-4 w-28 mx-auto bg-[#1e293b] rounded animate-pulse" />
      </div>
    </div>

    <!-- Not licensed -->
    <LoginPage
      v-else-if="!isLicensed"
      :has-password="hasPassword"
      :is-licensed="false"
      :hardware-fingerprint="hardwareFingerprint"
      @login="handleLogin"
      @activate-license="handleActivateLicense"
    />

    <!-- Licensed but not logged in (and password is set) -->
    <LoginPage
      v-else-if="!isLoggedIn && hasPassword"
      :has-password="true"
      :is-licensed="true"
      :hardware-fingerprint="hardwareFingerprint"
      @login="handleLogin"
      @activate-license="handleActivateLicense"
    />

    <!-- Auto login (no password) -->
    <template v-else-if="!isLoggedIn && !hasPassword">
      {{ isLoggedIn = true }}
    </template>

    <!-- Main layout -->
    <div v-else class="min-h-screen bg-[#0a192f]">
      <Sidebar
        :active-page="currentPage"
        @page-change="handlePageChange"
        @navigate-to-screen="navigateToScreen"
      />
      <div class="ml-[240px] min-h-screen flex flex-col">
        <Header :title="pageTitle" :store-name="storeName" />
        <main class="flex-1 p-6">
          <Dashboard
            v-if="currentPage === 'dashboard'"
            :dashboard-metrics="dashboardMetrics"
            :dashboard-metrics-labels="dashboardMetricsLabels"
          />
          <DeviceManagement v-else-if="currentPage === 'devices'" />
          <HistoryData v-else-if="currentPage === 'history'" />
          <SystemSettings v-else-if="currentPage === 'settings'" />
          <LargeScreenList v-else-if="currentPage === 'large-screen-settings'" />
          <LicenseSettings v-else-if="currentPage === 'license-settings'" />
        </main>
      </div>
    </div>
  </ConfigProvider>
</template>
