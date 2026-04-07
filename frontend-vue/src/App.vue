<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Toaster } from 'vue-sonner'
import { ConfigProvider } from 'ant-design-vue'
import { antdTheme } from '@/lib/antd-theme'
import Sidebar from '@/components/layout/Sidebar.vue'
import Header from '@/components/layout/Header.vue'
import Dashboard from '@/components/dashboard/Dashboard.vue'
import DeviceManagement from '@/components/devices/DeviceManagement.vue'
import HistoryData from '@/components/history/HistoryData.vue'
import SystemSettings from '@/components/settings/SystemSettings.vue'
import LargeScreenSettings from '@/components/settings/LargeScreenSettings.vue'
import LargeScreenView from '@/components/large-screen/LargeScreenView.vue'
import LoginPage from '@/components/auth/LoginPage.vue'

interface LicenseData {
  isActive: boolean
  hardwareFingerprint: string
  expiryDate: string
  maxDevices: number
}

interface SettingsData {
  storeName: string
  loginPassword: string
  dashboardMetrics: string
}

const pageTitles: Record<string, string> = {
  dashboard: '仪表盘',
  devices: '设备管理',
  history: '历史数据',
  settings: '系统设置',
  'large-screen-settings': '大屏设置',
}

const currentPage = ref('dashboard')
const isLoggedIn = ref(false)
const isLoading = ref(true)
const isLicensed = ref(false)
const hasPassword = ref(false)
const hardwareFingerprint = ref('')
const storeName = ref('我的门店')
const dashboardMetrics = ref('todayIn,todayOut,currentIn,weekIn')

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
      isLicensed.value = license.isActive
      hardwareFingerprint.value = license.hardwareFingerprint || ''
    }

    if (settingsRes.ok) {
      const settingsJson = await settingsRes.json()
      const settings: SettingsData = settingsJson.data || settingsJson
      storeName.value = settings.storeName || '我的门店'
      hasPassword.value = !!settings.loginPassword
      dashboardMetrics.value = settings.dashboardMetrics || 'todayIn,todayOut,currentIn,weekIn'
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
      isLicensed.value = license.isActive
    }
  } catch {
    // Handle error
  }
}

function handleLogin() {
  isLoggedIn.value = true
}

function handlePageChange(page: string) {
  currentPage.value = page
}

function navigateToScreen() {
  currentPage.value = 'large-screen'
}

function handleCloseLargeScreen() {
  currentPage.value = 'dashboard'
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

    <!-- Large screen mode -->
    <LargeScreenView
      v-else-if="currentPage === 'large-screen'"
      @close="handleCloseLargeScreen"
    />

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
          />
          <DeviceManagement v-else-if="currentPage === 'devices'" />
          <HistoryData v-else-if="currentPage === 'history'" />
          <SystemSettings v-else-if="currentPage === 'settings'" />
          <LargeScreenSettings v-else-if="currentPage === 'large-screen-settings'" />
        </main>
      </div>
    </div>

    <Toaster />
  </ConfigProvider>
</template>
