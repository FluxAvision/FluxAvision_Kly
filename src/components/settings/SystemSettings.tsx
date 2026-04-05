'use client'

import { useEffect, useState, useRef } from 'react'
import { Loader2, Upload, Save, ImageIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'

interface SettingsData {
  storeName: string
  storeLogo: string
  loginPassword: string
  dashboardMetrics: string[]
}

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

export default function SystemSettings() {
  const [settings, setSettings] = useState<SettingsData>({
    storeName: '我的门店',
    storeLogo: '',
    loginPassword: '',
    dashboardMetrics: ['todayIn', 'todayOut', 'currentIn', 'weekIn'],
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [newPassword, setNewPassword] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    async function fetchSettings() {
      try {
        const res = await fetch('/api/settings')
        if (res.ok) {
          const json = await res.json()
          const settingsData = json.data || json
          setSettings({
            storeName: settingsData.storeName || '我的门店',
            storeLogo: settingsData.storeLogo || '',
            loginPassword: settingsData.loginPassword || '',
            dashboardMetrics: settingsData.dashboardMetrics
              ? settingsData.dashboardMetrics.split(',')
              : ['todayIn', 'todayOut', 'currentIn', 'weekIn'],
          })
        }
      } catch {
        // Keep defaults
      } finally {
        setLoading(false)
      }
    }
    fetchSettings()
  }, [])

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = () => {
      setSettings((prev) => ({ ...prev, storeLogo: reader.result as string }))
    }
    reader.readAsDataURL(file)
  }

  const handleMetricToggle = (key: string) => {
    setSettings((prev) => {
      const metrics = [...prev.dashboardMetrics]
      const idx = metrics.indexOf(key)
      if (idx >= 0) {
        metrics.splice(idx, 1)
      } else if (metrics.length < MAX_METRICS) {
        metrics.push(key)
      }
      return { ...prev, dashboardMetrics: metrics }
    })
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const payload = {
        ...settings,
        dashboardMetrics: settings.dashboardMetrics.join(','),
        ...(newPassword ? { loginPassword: newPassword } : {}),
      }
      const res = await fetch('/api/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (res.ok) {
        setNewPassword('')
        setSettings((prev) => ({
          ...prev,
          ...(newPassword ? { loginPassword: newPassword } : {}),
        }))
      }
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="bg-[#112240] border border-[#1e293b] rounded-lg p-6"
          >
            <div className="h-5 w-32 bg-[#1e293b] rounded mb-4" />
            <div className="h-10 w-full bg-[#1e293b] rounded" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Store Name */}
      <div className="bg-[#112240] border border-[#1e293b] rounded-lg p-6">
        <h3 className="text-white font-medium mb-4">门店信息</h3>
        <div className="grid gap-4">
          <div className="grid gap-2">
            <Label className="text-[#8892a0]">门店名称</Label>
            <Input
              value={settings.storeName}
              onChange={(e) =>
                setSettings((prev) => ({ ...prev, storeName: e.target.value }))
              }
              placeholder="请输入门店名称"
              className="bg-[#0a192f] border-[#1e293b]"
            />
          </div>
          <div className="grid gap-2">
            <Label className="text-[#8892a0]">门店Logo</Label>
            <div className="flex items-center gap-4">
              {settings.storeLogo ? (
                <div className="w-16 h-16 rounded-lg border border-[#1e293b] overflow-hidden bg-[#0a192f] flex items-center justify-center">
                  <img
                    src={settings.storeLogo}
                    alt="Logo"
                    className="w-full h-full object-contain"
                  />
                </div>
              ) : (
                <div className="w-16 h-16 rounded-lg border border-dashed border-[#1e293b] flex items-center justify-center bg-[#0a192f]">
                  <ImageIcon className="w-6 h-6 text-[#8892a0]" aria-hidden="true" />
                </div>
              )}
              <div className="flex flex-col gap-2">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileUpload}
                  className="hidden"
                />
                <Button
                  variant="outline"
                  size="sm"
                  className="border-[#1e293b] text-[#8892a0] hover:text-white hover:bg-[#172a45]"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload className="w-4 h-4 mr-2" />
                  上传图片
                </Button>
                {settings.storeLogo && (
                  <button
                    onClick={() =>
                      setSettings((prev) => ({ ...prev, storeLogo: '' }))
                    }
                    className="text-xs text-[#ef4444] hover:underline cursor-pointer"
                  >
                    移除
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Login Password */}
      <div className="bg-[#112240] border border-[#1e293b] rounded-lg p-6">
        <h3 className="text-white font-medium mb-4">登录密码</h3>
        <div className="grid gap-4">
          <div className="flex items-center gap-3 text-sm">
            <span className="text-[#8892a0]">当前状态：</span>
            {settings.loginPassword ? (
              <span className="text-[#00ff88]">已设置密码</span>
            ) : (
              <span className="text-[#ff9500]">未设置密码</span>
            )}
          </div>
          <div className="grid gap-2">
            <Label className="text-[#8892a0]">新密码（留空则不修改）</Label>
            <Input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="输入新密码"
              className="bg-[#0a192f] border-[#1e293b]"
            />
          </div>
        </div>
      </div>

      {/* Dashboard Metrics */}
      <div className="bg-[#112240] border border-[#1e293b] rounded-lg p-6">
        <h3 className="text-white font-medium mb-1">仪表盘显示指标</h3>
        <p className="text-xs text-[#8892a0] mb-4">
          最多选择 {MAX_METRICS} 个指标显示在仪表盘上（已选{' '}
          {settings.dashboardMetrics.length}/{MAX_METRICS}）
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {metricOptions.map((opt) => {
            const checked = settings.dashboardMetrics.includes(opt.key)
            const disabled =
              !checked && settings.dashboardMetrics.length >= MAX_METRICS
            return (
              <label
                key={opt.key}
                className={`flex items-center gap-2.5 p-3 rounded-lg border cursor-pointer transition-colors ${
                  checked
                    ? 'border-[#00d9ff]/30 bg-[#00d9ff]/5'
                    : disabled
                      ? 'border-[#1e293b] bg-[#0a192f] opacity-50 cursor-not-allowed'
                      : 'border-[#1e293b] bg-[#0a192f] hover:border-[#1e293b]'
                }`}
              >
                <Checkbox
                  checked={checked}
                  disabled={disabled}
                  onCheckedChange={() => handleMetricToggle(opt.key)}
                  className="border-[#1e293b] data-[state=checked]:bg-[#00d9ff] data-[state=checked]:border-[#00d9ff]"
                />
                <span
                  className={`text-sm ${checked ? 'text-[#00d9ff]' : 'text-[#8892a0]'}`}
                >
                  {opt.label}
                </span>
              </label>
            )
          })}
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button
          onClick={handleSave}
          disabled={saving}
          className="bg-[#00d9ff] text-[#0a192f] hover:bg-[#00d9ff]/80 px-8"
        >
          {saving ? (
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Save className="w-4 h-4 mr-2" />
          )}
          保存设置
        </Button>
      </div>
    </div>
  )
}
