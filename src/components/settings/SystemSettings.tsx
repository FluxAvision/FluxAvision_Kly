'use client'

import { useEffect, useRef, useState } from 'react'
import { ImageIcon, Loader2, Save, Upload } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from '@/hooks/use-toast'

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
        if (!res.ok) {
          return
        }

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
      } catch {
        // 保持默认值
      } finally {
        setLoading(false)
      }
    }

    fetchSettings()
  }, [])

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) {
      return
    }

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
        toast({
          title: '保存成功',
          description: '系统设置已更新。',
        })
      } else {
        const json = await res.json().catch(() => null)
        toast({
          variant: 'destructive',
          title: '保存失败',
          description: json?.message || '系统设置保存失败，请稍后重试。',
        })
      }
    } catch {
      toast({
        variant: 'destructive',
        title: '保存失败',
        description: '系统设置保存失败，请检查网络或后端服务。',
      })
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="rounded-2xl border border-[#1e293b] bg-[#112240] p-6 sm:p-8">
        <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-6">
            {[1, 2].map((i) => (
              <div key={i} className="rounded-xl border border-[#1e293b] bg-[#0f1f3a] p-5">
                <div className="mb-4 h-5 w-32 rounded bg-[#1e293b]" />
                <div className="space-y-3">
                  <div className="h-10 rounded bg-[#1e293b]" />
                  <div className="h-24 rounded bg-[#1e293b]" />
                </div>
              </div>
            ))}
          </div>
          <div className="rounded-xl border border-[#1e293b] bg-[#0f1f3a] p-5">
            <div className="mb-4 h-5 w-40 rounded bg-[#1e293b]" />
            <div className="grid grid-cols-2 gap-3">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="h-14 rounded-lg bg-[#1e293b]" />
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  const selectedCount = settings.dashboardMetrics.length

  return (
    <div className="w-full">
      <div className="rounded-2xl border border-[#1e293b] bg-[#112240] p-6 shadow-[0_16px_50px_rgba(0,0,0,0.18)] sm:p-8">
        <div className="mb-6 flex flex-col gap-2 border-b border-[#1e293b] pb-5">
          <h2 className="text-2xl font-semibold tracking-tight text-white">系统设置</h2>
        </div>

        <div className="grid gap-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(360px,0.9fr)]">
          <div className="space-y-6">
            <section className="rounded-xl border border-[#1e293b] bg-[#0f1f3a] p-5 sm:p-6">
              <div className="mb-5">
                <h3 className="text-lg font-semibold text-white">门店信息</h3>
                <p className="mt-1 text-sm text-[#8aa0b8]">设置门店名称和门店 Logo，用于系统头部和页面展示。</p>
              </div>

              <div className="grid gap-5">
                <div className="grid gap-2">
                  <Label className="text-[#8aa0b8]">门店名称</Label>
                  <Input
                    value={settings.storeName}
                    onChange={(e) =>
                      setSettings((prev) => ({ ...prev, storeName: e.target.value }))
                    }
                    placeholder="请输入门店名称"
                    className="h-11 border-[#1e293b] bg-[#0a192f] text-white"
                  />
                </div>

                <div className="grid gap-3">
                  <Label className="text-[#8aa0b8]">门店 Logo</Label>
                  <div className="flex flex-col gap-4 rounded-xl border border-[#1e293b] bg-[#0a192f]/70 p-4 sm:flex-row sm:items-center">
                    {settings.storeLogo ? (
                      <div className="flex h-20 w-20 items-center justify-center overflow-hidden rounded-xl border border-[#1e293b] bg-[#091320] shadow-inner">
                        <img
                          src={settings.storeLogo}
                          alt="门店 Logo"
                          className="h-full w-full object-contain"
                        />
                      </div>
                    ) : (
                      <div className="flex h-20 w-20 items-center justify-center rounded-xl border border-dashed border-[#294261] bg-[#091320]">
                        <ImageIcon className="h-8 w-8 text-[#6f88a3]" aria-hidden="true" />
                      </div>
                    )}

                    <div className="min-w-0 flex-1 space-y-3">
                      <div>
                        <p className="text-sm font-medium text-white">上传品牌图标</p>
                        <p className="mt-1 text-xs text-[#8aa0b8]">建议使用透明背景的方形图片，便于头部和大屏场景复用。</p>
                      </div>

                      <div className="flex flex-wrap items-center gap-3">
                        <input
                          ref={fileInputRef}
                          type="file"
                          accept="image/*"
                          onChange={handleFileUpload}
                          className="hidden"
                        />
                        <Button
                          variant="outline"
                          className="border-[#294261] bg-[#112240] text-[#d6e4f0] hover:bg-[#173154] hover:text-white"
                          onClick={() => fileInputRef.current?.click()}
                        >
                          <Upload className="mr-2 h-4 w-4" />
                          上传图片
                        </Button>
                        {settings.storeLogo && (
                          <button
                            onClick={() => setSettings((prev) => ({ ...prev, storeLogo: '' }))}
                            className="text-sm text-[#ff7a7a] transition-colors hover:text-[#ff9f9f]"
                          >
                            移除图片
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <section className="rounded-xl border border-[#1e293b] bg-[#0f1f3a] p-5 sm:p-6">
              <div className="mb-5">
                <h3 className="text-lg font-semibold text-white">登录密码</h3>
                <p className="mt-1 text-sm text-[#8aa0b8]">为空则表示后台不需要二次登录，设置后将用于进入系统管理界面。</p>
              </div>

              <div className="grid gap-4">
                <div className="flex flex-wrap items-center gap-3 rounded-lg border border-[#1e293b] bg-[#0a192f]/70 px-4 py-3 text-sm">
                  <span className="text-[#8aa0b8]">当前状态</span>
                  {settings.loginPassword ? (
                    <span className="rounded-full bg-[#00ff88]/10 px-3 py-1 text-[#00ff88]">已设置密码</span>
                  ) : (
                    <span className="rounded-full bg-[#ff9500]/10 px-3 py-1 text-[#ffb44d]">未设置密码</span>
                  )}
                </div>

                <div className="grid gap-2">
                  <Label className="text-[#8aa0b8]">新密码</Label>
                  <Input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="留空则保持当前密码不变"
                    className="h-11 border-[#1e293b] bg-[#0a192f] text-white"
                  />
                </div>
              </div>
            </section>
          </div>

          <section className="flex h-full flex-col rounded-xl border border-[#1e293b] bg-[#0f1f3a] p-5 sm:p-6">
            <div className="mb-5">
              <h3 className="text-lg font-semibold text-white">仪表盘显示指标</h3>
              <p className="mt-1 text-sm text-[#8aa0b8]">
                最多选择 {MAX_METRICS} 个指标展示在仪表盘首页，当前已选择 {selectedCount}/{MAX_METRICS}。
              </p>
            </div>

            <div className="grid flex-1 grid-cols-1 gap-3 sm:grid-cols-2">
              {metricOptions.map((opt) => {
                const checked = settings.dashboardMetrics.includes(opt.key)
                const disabled = !checked && selectedCount >= MAX_METRICS

                return (
                  <label
                    key={opt.key}
                    className={`flex min-h-15 items-center gap-3 rounded-xl border px-4 py-3 transition-colors ${
                      checked
                        ? 'border-[#00d9ff]/40 bg-[#00d9ff]/10'
                        : disabled
                          ? 'cursor-not-allowed border-[#1e293b] bg-[#0a192f] opacity-45'
                          : 'cursor-pointer border-[#1e293b] bg-[#0a192f] hover:border-[#294261] hover:bg-[#10233f]'
                    }`}
                  >
                    <Checkbox
                      checked={checked}
                      disabled={disabled}
                      onCheckedChange={() => handleMetricToggle(opt.key)}
                      className="border-[#2d4765] data-[state=checked]:border-[#00d9ff] data-[state=checked]:bg-[#00d9ff]"
                    />
                    <div className="min-w-0">
                      <p className={`text-sm font-medium ${checked ? 'text-[#00d9ff]' : 'text-[#d6e4f0]'}`}>
                        {opt.label}
                      </p>
                      <p className="mt-1 text-xs text-[#6f88a3]">
                        {checked ? '已加入首页展示' : disabled ? '已达到可选上限' : '点击加入首页展示'}
                      </p>
                    </div>
                  </label>
                )
              })}
            </div>
          </section>
        </div>

        <div className="mt-6 flex items-center justify-end border-t border-[#1e293b] pt-5">
          <Button
            onClick={handleSave}
            disabled={saving}
            className="min-w-36 bg-[#00d9ff] px-8 text-[#0a192f] hover:bg-[#00d9ff]/80"
          >
            {saving ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Save className="mr-2 h-4 w-4" />
            )}
            保存设置
          </Button>
        </div>
      </div>
    </div>
  )
}
