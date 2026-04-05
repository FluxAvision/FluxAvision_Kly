'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Upload,
  Save,
  Loader2,
  Copy,
  Check,
  ImageIcon,
  Shield,
  Monitor,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from '@/hooks/use-toast'

interface Device {
  id: string
  name: string
  status: string
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

interface LicenseInfo {
  hardwareFingerprint: string
  isActive: boolean
  expiryDate: string
  maxDevices: number
}

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

const templates = [
  { id: 'tpl-blue', name: '经典蓝', color: '#1e3a5f', desc: '沉稳清晰，适合门店和商用展示' },
  { id: 'tpl-tech', name: '科技感', color: '#00d9ff', desc: '高亮对比，更突出实时数据变化' },
  { id: 'tpl-minimal', name: '简约风', color: '#8892a0', desc: '信息克制，适合长期运行展示' },
  { id: 'tpl-data', name: '数据驱动', color: '#00ff88', desc: '强化指标卡片，聚焦经营看板' },
]

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

function ConfigCard({
  title,
  subtitle,
  children,
  className = '',
}: {
  title: string
  subtitle?: string
  children: React.ReactNode
  className?: string
}) {
  return (
    <section className={`rounded-lg border border-[#1e293b] bg-[#112240] p-6 ${className}`}>
      <div className="mb-4">
        <h3 className="text-white font-medium">{title}</h3>
        {subtitle ? <p className="mt-1 text-sm text-[#8892a0]">{subtitle}</p> : null}
      </div>
      {children}
    </section>
  )
}

export default function LargeScreenSettings() {
  const [config, setConfig] = useState<LargeScreenConfig>(DEFAULT_CONFIG)
  const [license, setLicense] = useState<LicenseInfo>({
    hardwareFingerprint: '',
    isActive: false,
    expiryDate: '',
    maxDevices: 4,
  })
  const [devices, setDevices] = useState<Device[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [activating, setActivating] = useState(false)
  const [activationCode, setActivationCode] = useState('')
  const [copied, setCopied] = useState(false)

  const logoInputRef = useRef<HTMLInputElement>(null)
  const bgInputRef = useRef<HTMLInputElement>(null)

  const fetchAll = useCallback(async () => {
    try {
      const [settingsRes, devicesRes, licenseRes] = await Promise.all([
        fetch('/api/large-screen'),
        fetch('/api/devices'),
        fetch('/api/license'),
      ])

      if (settingsRes.ok) {
        const json = await settingsRes.json()
        const settingsData = json.data || json
        setConfig({
          title: settingsData.title || DEFAULT_CONFIG.title,
          subtitle: settingsData.subtitle || DEFAULT_CONFIG.subtitle,
          logo: settingsData.logo || '',
          backgroundImage: settingsData.backgroundImage || '',
          metrics: settingsData.metrics
            ? settingsData.metrics.split(',').filter(Boolean)
            : DEFAULT_CONFIG.metrics,
          deviceIds: settingsData.deviceIds
            ? settingsData.deviceIds.split(',').filter(Boolean)
            : [],
          templateId: settingsData.templateId || '',
        })
      }

      if (devicesRes.ok) {
        const json = await devicesRes.json()
        const devicesData = json.data || json
        setDevices(Array.isArray(devicesData) ? devicesData : [])
      }

      if (licenseRes.ok) {
        const json = await licenseRes.json()
        const licenseData = json.data || json
        setLicense(licenseData)
      }
    } catch {
      // 保持默认值
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  const handleSave = async () => {
    setSaving(true)
    try {
      const res = await fetch('/api/large-screen', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...config,
          metrics: config.metrics.join(','),
          deviceIds: config.deviceIds.join(','),
        }),
      })

      if (res.ok) {
        toast({
          title: '保存成功',
          description: '大屏配置已更新。',
        })
      } else {
        const json = await res.json().catch(() => null)
        toast({
          variant: 'destructive',
          title: '保存失败',
          description: json?.message || '大屏配置保存失败，请稍后重试。',
        })
      }
    } catch {
      toast({
        variant: 'destructive',
        title: '保存失败',
        description: '大屏配置保存失败，请检查网络或后端服务。',
      })
    } finally {
      setSaving(false)
    }
  }

  const handleActivate = async () => {
    if (!activationCode.trim()) return

    setActivating(true)
    try {
      const res = await fetch('/api/license', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ activationCode: activationCode.trim() }),
      })

      if (res.ok) {
        const json = await res.json()
        const licenseData = json.data || json
        setLicense(licenseData)
        setActivationCode('')
        toast({
          title: '激活成功',
          description: '离线授权已生效。',
        })
      } else {
        const json = await res.json().catch(() => null)
        toast({
          variant: 'destructive',
          title: '激活失败',
          description: json?.message || '激活码无效或已失效。',
        })
      }
    } catch {
      toast({
        variant: 'destructive',
        title: '激活失败',
        description: '授权请求失败，请稍后重试。',
      })
    } finally {
      setActivating(false)
    }
  }

  const handleTemplateSelect = async (tplId: string) => {
    const newConfig = { ...config, templateId: tplId }
    setConfig(newConfig)

    try {
      const res = await fetch('/api/large-screen', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...newConfig,
          metrics: newConfig.metrics.join(','),
          deviceIds: newConfig.deviceIds.join(','),
        }),
      })

      if (!res.ok) {
        const json = await res.json().catch(() => null)
        toast({
          variant: 'destructive',
          title: '模板切换失败',
          description: json?.message || '模板保存失败，请稍后重试。',
        })
        return
      }

      toast({
        title: '模板已切换',
        description: '大屏模板配置已更新。',
      })
    } catch {
      toast({
        variant: 'destructive',
        title: '模板切换失败',
        description: '模板保存失败，请检查网络或后端服务。',
      })
    }
  }

  const handleCopyFingerprint = () => {
    navigator.clipboard.writeText(license.hardwareFingerprint)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDeviceToggle = (deviceId: string) => {
    setConfig((prev) => {
      const ids = [...prev.deviceIds]
      const index = ids.indexOf(deviceId)
      if (index >= 0) {
        ids.splice(index, 1)
      } else if (ids.length < MAX_SCREEN_DEVICES) {
        ids.push(deviceId)
      }
      return { ...prev, deviceIds: ids }
    })
  }

  const handleMetricToggle = (key: string) => {
    setConfig((prev) => {
      const metrics = [...prev.metrics]
      const index = metrics.indexOf(key)
      if (index >= 0) {
        metrics.splice(index, 1)
      } else if (metrics.length < MAX_SCREEN_METRICS) {
        metrics.push(key)
      }
      return { ...prev, metrics }
    })
  }

  const handleFileUpload = (
    field: 'logo' | 'backgroundImage',
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = () => {
      setConfig((prev) => ({ ...prev, [field]: reader.result as string }))
    }
    reader.readAsDataURL(file)
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-96 bg-[#1e293b]" />
        <Skeleton className="h-[520px] w-full bg-[#1e293b]" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Tabs defaultValue="general" className="w-full">
        <TabsList className="border border-[#1e293b] bg-[#112240]">
          <TabsTrigger
            value="general"
            className="text-[#8892a0] data-[state=active]:bg-[#00d9ff] data-[state=active]:text-[#0a192f]"
          >
            通用配置
          </TabsTrigger>
          <TabsTrigger
            value="templates"
            className="text-[#8892a0] data-[state=active]:bg-[#00d9ff] data-[state=active]:text-[#0a192f]"
          >
            大屏模板
          </TabsTrigger>
          <TabsTrigger
            value="license"
            className="text-[#8892a0] data-[state=active]:bg-[#00d9ff] data-[state=active]:text-[#0a192f]"
          >
            License管理
          </TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="mt-6">
          <div className="grid gap-6 xl:grid-cols-[minmax(0,1.18fr)_minmax(360px,0.82fr)]">
            <div className="space-y-6">
              <ConfigCard title="大屏基础信息">
                <div className="grid gap-4 lg:grid-cols-2">
                  <div className="grid gap-2">
                    <Label className="text-[#8892a0]">大屏标题</Label>
                    <Input
                      value={config.title}
                      onChange={(e) =>
                        setConfig((prev) => ({ ...prev, title: e.target.value }))
                      }
                      className="border-[#1e293b] bg-[#0a192f]"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label className="text-[#8892a0]">大屏副标题</Label>
                    <Input
                      value={config.subtitle}
                      onChange={(e) =>
                        setConfig((prev) => ({ ...prev, subtitle: e.target.value }))
                      }
                      className="border-[#1e293b] bg-[#0a192f]"
                    />
                  </div>
                </div>
              </ConfigCard>

              <ConfigCard
                title="数据指标"
                subtitle={`最多选择 ${MAX_SCREEN_METRICS} 个指标，当前已选择 ${config.metrics.length} 个。`}
              >
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                  {metricOptions.map((option) => {
                    const checked = config.metrics.includes(option.key)
                    const disabled = !checked && config.metrics.length >= MAX_SCREEN_METRICS
                    return (
                      <label
                        key={option.key}
                        className={`flex items-center gap-2.5 rounded-lg border p-3 transition-colors ${
                          checked
                            ? 'border-[#00d9ff]/30 bg-[#00d9ff]/5'
                            : disabled
                              ? 'cursor-not-allowed border-[#1e293b] bg-[#0a192f] opacity-50'
                              : 'cursor-pointer border-[#1e293b] bg-[#0a192f] hover:border-[#29415f]'
                        }`}
                      >
                        <Checkbox
                          checked={checked}
                          disabled={disabled}
                          onCheckedChange={() => handleMetricToggle(option.key)}
                          className="border-[#1e293b] data-[state=checked]:border-[#00d9ff] data-[state=checked]:bg-[#00d9ff]"
                        />
                        <span className={`text-sm ${checked ? 'text-[#00d9ff]' : 'text-[#8892a0]'}`}>
                          {option.label}
                        </span>
                      </label>
                    )
                  })}
                </div>
              </ConfigCard>
            </div>

            <div className="space-y-6">
              <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-1">
                <ConfigCard title="大屏 LOGO" subtitle="建议上传透明背景的正方形图片，便于在头部区域展示。">
                  <div className="flex items-center gap-4">
                    {config.logo ? (
                      <div className="h-20 w-20 overflow-hidden rounded-lg border border-[#1e293b] bg-[#0a192f]">
                        <img src={config.logo} alt="Logo" className="h-full w-full object-contain" />
                      </div>
                    ) : (
                      <div className="flex h-20 w-20 items-center justify-center rounded-lg border border-dashed border-[#1e293b] bg-[#0a192f]">
                        <ImageIcon className="h-6 w-6 text-[#8892a0]" aria-hidden="true" />
                      </div>
                    )}
                    <div className="flex flex-col gap-2">
                      <input
                        ref={logoInputRef}
                        type="file"
                        accept="image/*"
                        onChange={(e) => handleFileUpload('logo', e)}
                        className="hidden"
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        className="border-[#1e293b] text-[#8892a0] hover:bg-[#172a45] hover:text-white"
                        onClick={() => logoInputRef.current?.click()}
                      >
                        <Upload className="mr-2 h-4 w-4" />
                        上传LOGO
                      </Button>
                      {config.logo ? (
                        <button
                          onClick={() => setConfig((prev) => ({ ...prev, logo: '' }))}
                          className="text-left text-xs text-[#ef4444] hover:underline"
                        >
                          移除
                        </button>
                      ) : null}
                    </div>
                  </div>
                </ConfigCard>

                <ConfigCard title="大屏背景图" subtitle="可上传氛围背景图，让大屏展示更完整。">
                  <div className="flex items-center gap-4">
                    {config.backgroundImage ? (
                      <div className="h-24 w-36 overflow-hidden rounded-lg border border-[#1e293b] bg-[#0a192f]">
                        <img
                          src={config.backgroundImage}
                          alt="背景图"
                          className="h-full w-full object-cover"
                        />
                      </div>
                    ) : (
                      <div className="flex h-24 w-36 items-center justify-center rounded-lg border border-dashed border-[#1e293b] bg-[#0a192f]">
                        <ImageIcon className="h-6 w-6 text-[#8892a0]" aria-hidden="true" />
                      </div>
                    )}
                    <div className="flex flex-col gap-2">
                      <input
                        ref={bgInputRef}
                        type="file"
                        accept="image/*"
                        onChange={(e) => handleFileUpload('backgroundImage', e)}
                        className="hidden"
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        className="border-[#1e293b] text-[#8892a0] hover:bg-[#172a45] hover:text-white"
                        onClick={() => bgInputRef.current?.click()}
                      >
                        <Upload className="mr-2 h-4 w-4" />
                        上传背景图
                      </Button>
                      {config.backgroundImage ? (
                        <button
                          onClick={() =>
                            setConfig((prev) => ({ ...prev, backgroundImage: '' }))
                          }
                          className="text-left text-xs text-[#ef4444] hover:underline"
                        >
                          移除
                        </button>
                      ) : null}
                    </div>
                  </div>
                </ConfigCard>
              </div>

              <ConfigCard
                title="实时视频设备"
                subtitle={`最多选择 ${MAX_SCREEN_DEVICES} 台设备，当前已选择 ${config.deviceIds.length} 台。`}
              >
                {devices.length === 0 ? (
                  <p className="text-sm text-[#8892a0]">暂无可用设备</p>
                ) : (
                  <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-1">
                    {devices.map((device) => {
                      const checked = config.deviceIds.includes(device.id)
                      const disabled = !checked && config.deviceIds.length >= MAX_SCREEN_DEVICES
                      return (
                        <label
                          key={device.id}
                          className={`flex items-center gap-2.5 rounded-lg border p-3 transition-colors ${
                            checked
                              ? 'border-[#00d9ff]/30 bg-[#00d9ff]/5'
                              : disabled
                                ? 'cursor-not-allowed border-[#1e293b] bg-[#0a192f] opacity-50'
                                : 'cursor-pointer border-[#1e293b] bg-[#0a192f] hover:border-[#29415f]'
                          }`}
                        >
                          <Checkbox
                            checked={checked}
                            disabled={disabled}
                            onCheckedChange={() => handleDeviceToggle(device.id)}
                            className="border-[#1e293b] data-[state=checked]:border-[#00d9ff] data-[state=checked]:bg-[#00d9ff]"
                          />
                          <div className="min-w-0">
                            <p className={`truncate text-sm ${checked ? 'text-[#00d9ff]' : 'text-white'}`}>
                              {device.name}
                            </p>
                            <p className="text-xs text-[#8892a0]">
                              {device.status === 'online' ? '在线' : '离线'}
                            </p>
                          </div>
                        </label>
                      )
                    })}
                  </div>
                )}
              </ConfigCard>

              <ConfigCard
                title="保存配置"
                className="xl:sticky xl:top-6"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <p className="text-sm text-white">当前已配置的展示信息会立即用于大屏预览。</p>
                    <p className="text-xs text-[#8892a0]">
                      指标已选 {config.metrics.length} 项，设备已选 {config.deviceIds.length} 台。
                    </p>
                  </div>
                  <Badge className="border-[#00d9ff]/20 bg-[#00d9ff]/10 text-[#00d9ff]">
                    Ready
                  </Badge>
                </div>
                <Button
                  onClick={handleSave}
                  disabled={saving}
                  className="mt-4 h-11 w-full bg-[#00d9ff] text-[#0a192f] hover:bg-[#00d9ff]/80"
                >
                  {saving ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="mr-2 h-4 w-4" />
                  )}
                  保存配置
                </Button>
              </ConfigCard>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="templates" className="mt-6 space-y-6">
          <ConfigCard title="大屏模板" subtitle="点击卡片即可切换模板，适合快速预览不同风格。">
            <div className="mb-6 flex items-center justify-between">
              <div className="text-sm text-[#8892a0]">模板切换会自动保存到当前大屏配置中。</div>
              {config.templateId ? (
                <Badge className="border-[#00d9ff]/20 bg-[#00d9ff]/10 text-[#00d9ff]">
                  当前使用中
                </Badge>
              ) : null}
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {templates.map((template) => {
                const selected = config.templateId === template.id
                return (
                  <button
                    key={template.id}
                    type="button"
                    onClick={() => handleTemplateSelect(template.id)}
                    className={`overflow-hidden rounded-lg border text-left transition-all ${
                      selected
                        ? 'border-[#00d9ff] shadow-lg shadow-[#00d9ff]/10'
                        : 'border-[#1e293b] hover:border-[#00d9ff]/30'
                    }`}
                  >
                    <div
                      className="relative flex h-36 items-center justify-center"
                      style={{
                        background: `linear-gradient(135deg, ${template.color}40, ${template.color}10)`,
                      }}
                    >
                      <Monitor className="h-12 w-12" style={{ color: template.color }} />
                      {selected ? (
                        <div className="absolute right-2 top-2 rounded-full bg-[#00d9ff] p-1">
                          <Check className="h-3 w-3 text-[#0a192f]" />
                        </div>
                      ) : null}
                    </div>
                    <div className="bg-[#0a192f] p-4">
                      <h4 className="text-sm font-medium text-white">{template.name}</h4>
                      <p className="mt-1 text-xs text-[#8892a0]">{template.desc}</p>
                    </div>
                  </button>
                )
              })}
            </div>
          </ConfigCard>
        </TabsContent>

        <TabsContent value="license" className="mt-6">
          <ConfigCard title="License 管理" subtitle="用于查看授权状态、复制硬件指纹和执行离线激活。">
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <Shield className="h-5 w-5 text-[#8892a0]" />
                <span
                  className={`text-sm font-medium ${
                    license.isActive ? 'text-[#00ff88]' : 'text-[#ff9500]'
                  }`}
                >
                  {license.isActive ? '已激活' : '未激活'}
                </span>
              </div>

              <div className="grid gap-2">
                <Label className="text-[#8892a0]">硬件指纹</Label>
                <div className="flex gap-2">
                  <Input
                    readOnly
                    value={license.hardwareFingerprint || '加载中...'}
                    className="border-[#1e293b] bg-[#0a192f] font-mono text-xs"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    className="shrink-0 border-[#1e293b] text-[#8892a0] hover:bg-[#172a45] hover:text-white"
                    onClick={handleCopyFingerprint}
                  >
                    {copied ? (
                      <Check className="h-4 w-4 text-[#00ff88]" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>

              {license.isActive ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="rounded-lg border border-[#1e293b] bg-[#0a192f] p-4">
                    <p className="mb-1 text-xs text-[#8892a0]">授权到期时间</p>
                    <p className="text-sm font-medium text-white">{license.expiryDate || '永久'}</p>
                  </div>
                  <div className="rounded-lg border border-[#1e293b] bg-[#0a192f] p-4">
                    <p className="mb-1 text-xs text-[#8892a0]">最大设备数</p>
                    <p className="text-sm font-medium text-white">{license.maxDevices} 台</p>
                  </div>
                </div>
              ) : null}

              <div className="grid gap-2">
                <Label className="text-[#8892a0]">离线激活</Label>
                <Textarea
                  value={activationCode}
                  onChange={(e) => setActivationCode(e.target.value)}
                  placeholder="请输入或粘贴激活码..."
                  className="min-h-[120px] border-[#1e293b] bg-[#0a192f] font-mono text-xs"
                />
              </div>

              <Button
                onClick={handleActivate}
                disabled={activating || !activationCode.trim()}
                className="w-fit bg-[#00d9ff] text-[#0a192f] hover:bg-[#00d9ff]/80"
              >
                {activating ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Shield className="mr-2 h-4 w-4" />
                )}
                激活
              </Button>
            </div>
          </ConfigCard>
        </TabsContent>
      </Tabs>
    </div>
  )
}
