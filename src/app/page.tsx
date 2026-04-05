'use client'

import { useEffect, useState, useCallback } from 'react'
import Sidebar from '@/components/layout/Sidebar'
import Header from '@/components/layout/Header'
import Dashboard from '@/components/dashboard/Dashboard'
import DeviceManagement from '@/components/devices/DeviceManagement'
import HistoryData from '@/components/history/HistoryData'
import SystemSettings from '@/components/settings/SystemSettings'
import LargeScreenSettings from '@/components/settings/LargeScreenSettings'
import LargeScreenView from '@/components/large-screen/LargeScreenView'
import LoginPage from '@/components/auth/LoginPage'
import { Skeleton } from '@/components/ui/skeleton'

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

export default function Home() {
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isLicensed, setIsLicensed] = useState(false)
  const [hasPassword, setHasPassword] = useState(false)
  const [hardwareFingerprint, setHardwareFingerprint] = useState('')
  const [storeName, setStoreName] = useState('我的门店')
  const [dashboardMetrics, setDashboardMetrics] = useState('todayIn,todayOut,currentIn,weekIn')

  const checkSystemStatus = useCallback(async () => {
    try {
      const [licenseRes, settingsRes] = await Promise.all([
        fetch('/api/license'),
        fetch('/api/settings'),
      ])

      if (licenseRes.ok) {
        const licenseJson = await licenseRes.json()
        const license: LicenseData = licenseJson.data || licenseJson
        setIsLicensed(license.isActive)
        setHardwareFingerprint(license.hardwareFingerprint || '')
      }

      if (settingsRes.ok) {
        const settingsJson = await settingsRes.json()
        const settings: SettingsData = settingsJson.data || settingsJson
        setStoreName(settings.storeName || '我的门店')
        setHasPassword(!!settings.loginPassword)
        setDashboardMetrics(settings.dashboardMetrics || 'todayIn,todayOut,currentIn,weekIn')
      }
    } catch {
      // Keep defaults
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    checkSystemStatus()
  }, [checkSystemStatus])

  const handleLogin = () => {
    setIsLoggedIn(true)
  }

  const handleActivateLicense = async (code: string) => {
    try {
      const res = await fetch('/api/license', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ activationCode: code }),
      })
      if (res.ok) {
        const json = await res.json()
        const license = json.data || json
        setIsLicensed(license.isActive)
      }
    } catch {
      // Handle error
    }
  }

  const handlePageChange = (page: string) => {
    setCurrentPage(page)
  }

  const handleNavigateToScreen = () => {
    setCurrentPage('large-screen')
  }

  const handleCloseLargeScreen = () => {
    setCurrentPage('dashboard')
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0a192f] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 rounded-xl bg-[#00d9ff]/10 flex items-center justify-center mx-auto mb-4">
            <Skeleton className="w-8 h-8 rounded-lg bg-[#1e293b]" />
          </div>
          <Skeleton className="h-6 w-40 mx-auto mb-2 bg-[#1e293b]" />
          <Skeleton className="h-4 w-28 mx-auto bg-[#1e293b]" />
        </div>
      </div>
    )
  }

  // Not licensed - show license activation
  if (!isLicensed) {
    return (
      <LoginPage
        onLogin={handleLogin}
        hasPassword={hasPassword}
        isLicensed={false}
        onActivateLicense={handleActivateLicense}
        hardwareFingerprint={hardwareFingerprint}
      />
    )
  }

  // Licensed but not logged in (and password is set)
  if (!isLoggedIn && hasPassword) {
    return (
      <LoginPage
        onLogin={handleLogin}
        hasPassword={true}
        isLicensed={true}
        onActivateLicense={handleActivateLicense}
        hardwareFingerprint={hardwareFingerprint}
      />
    )
  }

  // Licensed and no password - auto login
  if (!isLoggedIn && !hasPassword) {
    setIsLoggedIn(true)
    // Return loading to avoid flash
    return null
  }

  // Large screen mode - full screen overlay
  if (currentPage === 'large-screen') {
    return <LargeScreenView onClose={handleCloseLargeScreen} />
  }

  // Main layout
  return (
    <div className="min-h-screen bg-[#0a192f]">
      <Sidebar
        activePage={currentPage}
        onPageChange={handlePageChange}
        onNavigateToScreen={handleNavigateToScreen}
      />
      <div className="ml-[240px] min-h-screen flex flex-col">
        <Header
          title={pageTitles[currentPage] || '仪表盘'}
          storeName={storeName}
        />
        <main className="flex-1 p-6">
          {currentPage === 'dashboard' && (
            <Dashboard dashboardMetrics={dashboardMetrics} />
          )}
          {currentPage === 'devices' && <DeviceManagement />}
          {currentPage === 'history' && <HistoryData />}
          {currentPage === 'settings' && <SystemSettings />}
          {currentPage === 'large-screen-settings' && (
            <LargeScreenSettings />
          )}
        </main>
      </div>
    </div>
  )
}
