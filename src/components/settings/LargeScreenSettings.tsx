'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
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

const MAX_SCREEN_METRICS = 4

const templates = [
  { id: 'tpl-blue', name: '经典蓝', color: '#1e3a5f', desc: '沉稳大气的蓝色主题' },
  { id: 'tpl-tech', name: '科技感', color: '#00d9ff', desc: '充满科技感的设计' },
  { id: 'tpl-minimal', name: '简约风', color: '#8892a0', desc: '简约而不简单' },
  { id: 'tpl-data', name: '数据驱动', color: '#00ff88', desc: '突出数据展示' },
]

export default function LargeScreenSettings() {
  const [config, setConfig] = useState<LargeScreenConfig>({
    title: '客流统计大屏',
    subtitle: '实时客流数据展示',
    logo: '',
    backgroundImage: '',
    metrics: ['todayIn', 'todayOut', 'currentIn'],
    deviceIds: [],
    templateId: '',
  })
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
          title: settingsData.title || '客流统计大屏',
          subtitle: settingsData.subtitle || '实时客流数据展示',
          logo: settingsData.logo || '',
          backgroundImage: settingsData.backgroundImage || '',
          metrics: settingsData.metrics ? settingsData.metrics.split(',') : ['todayIn', 'todayOut', 'currentIn'],
          deviceIds: settingsData.deviceIds ? settingsData.deviceIds.split(',').filter(Boolean) : [],
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
      // Keep defaults
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
      await fetch('/api/large-screen', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...config,
          metrics: config.metrics.join(','),
          deviceIds: config.deviceIds.join(','),
        }),
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
      }
    } finally {
      setActivating(false)
    }
  }

  // 模板可随时切换，直接保存
  const handleTemplateSelect = async (tplId: string) => {
    const newConfig = { ...config, templateId: tplId }
    setConfig(newConfig)
    try {
      await fetch('/api/large-screen', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...newConfig,
          metrics: newConfig.metrics.join(','),
          deviceIds: newConfig.deviceIds.join(','),
        }),
      })
    } catch {
      // Ignore
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
      const idx = ids.indexOf(deviceId)
      if (idx >= 0) {
        ids.splice(idx, 1)
      } else if (ids.length < 4) {
        ids.push(deviceId)
      }
      return { ...prev, deviceIds: ids }
    })
  }

  const handleMetricToggle = (key: string) => {
    setConfig((prev) => {
      const metrics = [...prev.metrics]
      const idx = metrics.indexOf(key)
      if (idx >= 0) {
        metrics.splice(idx, 1)
      } else if (metrics.length < MAX_SCREEN_METRICS) {
        metrics.push(key)
      }
      return { ...prev, metrics }
    })
  }

  const handleFileUpload = (
    field: 'logo' | 'backgroundImage',
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = e.target.files?.[0]
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
        <Skeleton className="h-[500px] w-full bg-[#1e293b]" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Tabs defaultValue="general" className="w-full">
        <TabsList className="bg-[#112240] border border-[#1e293b]">
          <TabsTrigger
            value="general"
            className="data-[state=active]:bg-[#00d9ff] data-[state=active]:text-[#0a192f] text-[#8892a0]"
          >
            通用配置
          </TabsTrigger>
          <TabsTrigger
            value="templates"
            className="data-[state=active]:bg-[#00d9ff] data-[state=active]:text-[#0a192f] text-[#8892a0]"
          >
            大屏模板
          </TabsTrigger>
          <TabsTrigger
            value="license"
            className="data-[state=active]:bg-[#00d9ff] data-[state=active]:text-[#0a192f] text-[#8892a0]"
          >
            License管理
          </TabsTrigger>
        </TabsList>

        {/* Tab 1: General Config */}
        <TabsContent value="general" className="space-y-6 mt-6">
          <div className="bg-[#112240] border border-[#1e293b] rounded-lg p-6 max-w-2xl space-y-4">
            <h3 className="text-white font-medium">大屏基础信息</h3>
            <div className="grid gap-2">
              <Label className="text-[#8892a0]">大屏标题</Label>
              <Input
                value={config.title}
                onChange={(e) =>
                  setConfig((prev) => ({ ...prev, title: e.target.value }))
                }
                className="bg-[#0a192f] border-[#1e293b]"
              />
            </div>
            <div className="grid gap-2">
              <Label className="text-[#8892a0]">大屏副标题</Label>
              <Input
                value={config.subtitle}
                onChange={(e) =>
                  setConfig((prev) => ({ ...prev, subtitle: e.target.value }))
                }
                className="bg-[#0a192f] border-[#1e293b]"
              />
            </div>
          </div>

          <div className="bg-[#112240] border border-[#1e293b] rounded-lg p-6 max-w-2xl space-y-4">
            <h3 className="text-white font-medium">大屏LOGO</h3>
            <div className="flex items-center gap-4">
              {config.logo ? (
                <div className="w-16 h-16 rounded-lg border border-[#1e293b] overflow-hidden bg-[#0a192f]">
                  <img src={config.logo} alt="Logo" className="w-full h-full object-contain" />
                </div>
              ) : (
                <div className="w-16 h-16 rounded-lg border border-dashed border-[#1e293b] flex items-center justify-center bg-[#0a192f]">
                  <ImageIcon className="w-6 h-6 text-[#8892a0]" aria-hidden="true" />
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
                  className="border-[#1e293b] text-[#8892a0] hover:text-white hover:bg-[#172a45]"
                  onClick={() => logoInputRef.current?.click()}
                >
                  <Upload className="w-4 h-4 mr-2" />
                  上传LOGO
                </Button>
                {config.logo && (
                  <button
                    onClick={() => setConfig((prev) => ({ ...prev, logo: '' }))}
                    className="text-xs text-[#ef4444] hover:underline cursor-pointer"
                  >
                    移除
                  </button>
                )}
              </div>
            </div>
          </div>

          <div className="bg-[#112240] border border-[#1e293b] rounded-lg p-6 max-w-2xl space-y-4">
            <h3 className="text-white font-medium">大屏背景图</h3>
            <div className="flex items-center gap-4">
              {config.backgroundImage ? (
                <div className="w-32 h-20 rounded-lg border border-[#1e293b] overflow-hidden bg-[#0a192f]">
                  <img src={config.backgroundImage} alt="背景图" className="w-full h-full object-cover" />
                </div>
              ) : (
                <div className="w-32 h-20 rounded-lg border border-dashed border-[#1e293b] flex items-center justify-center bg-[#0a192f]">
                  <ImageIcon className="w-6 h-6 text-[#8892a0]" aria-hidden="true" />
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
                  className="border-[#1e293b] text-[#8892a0] hover:text-white hover:bg-[#172a45]"
                  onClick={() => bgInputRef.current?.click()}
                >
                  <Upload className="w-4 h-4 mr-2" />
                  上传背景图
                </Button>
                {config.backgroundImage && (
                  <button
                    onClick={() =>
                      setConfig((prev) => ({ ...prev, backgroundImage: '' }))
                    }
                    className="text-xs text-[#ef4444] hover:underline cursor-pointer"
                  >
                    移除
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* 数据指标 - 可自由选择，最多4个 */}
          <div className="bg-[#112240] border border-[#1e293b] rounded-lg p-6 max-w-2xl space-y-4">
            <h3 className="text-white font-medium">
              数据指标
              <span className="text-xs text-[#8892a0] ml-2">
                最多选择 {MAX_SCREEN_METRICS} 个（已选 {config.metrics.length}/{MAX_SCREEN_METRICS}）
              </span>
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {metricOptions.map((opt) => {
                const checked = config.metrics.includes(opt.key)
                const disabled = !checked && config.metrics.length >= MAX_SCREEN_METRICS
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
                    <span className={`text-sm ${checked ? 'text-[#00d9ff]' : 'text-[#8892a0]'}`}>
                      {opt.label}
                    </span>
                  </label>
                )
              })}
            </div>
          </div>

          {/* 实时视频设备 */}
          <div className="bg-[#112240] border border-[#1e293b] rounded-lg p-6 max-w-2xl space-y-4">
            <h3 className="text-white font-medium">
              实时视频设备
              <span className="text-xs text-[#8892a0] ml-2">
                最多选择 4 个（已选 {config.deviceIds.length}/4）
              </span>
            </h3>
            {devices.length === 0 ? (
              <p className="text-sm text-[#8892a0]">暂无可用设备</p>
            ) : (
              <div className="grid grid-cols-2 gap-3">
                {devices.map((device) => {
                  const checked = config.deviceIds.includes(device.id)
                  const disabled = !checked && config.deviceIds.length >= 4
                  return (
                    <label
                      key={device.id}
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
                        onCheckedChange={() => handleDeviceToggle(device.id)}
                        className="border-[#1e293b] data-[state=checked]:bg-[#00d9ff] data-[state=checked]:border-[#00d9ff]"
                      />
                      <div className="min-w-0">
                        <p className={`text-sm truncate ${checked ? 'text-[#00d9ff]' : 'text-white'}`}>
                          {device.name}
                        </p>
                        <p className="text-xs text-[#8892a0]">{device.status === 'online' ? '在线' : '离线'}</p>
                      </div>
                    </label>
                  )
                })}
              </div>
            )}
          </div>

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
              保存配置
            </Button>
          </div>
        </TabsContent>

        {/* Tab 2: Templates - 可随时切换 */}
        <TabsContent value="templates" className="space-y-6 mt-6">
          <div className="bg-[#112240] border border-[#1e293b] rounded-lg p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-white font-medium">大屏模板</h3>
                <p className="text-xs text-[#8892a0] mt-1">
                  点击即可切换大屏模板，可随时更换
                </p>
              </div>
              {config.templateId && (
                <Badge className="bg-[#00d9ff]/10 text-[#00d9ff] border-[#00d9ff]/20">
                  当前使用中
                </Badge>
              )}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {templates.map((tpl) => {
                const isSelected = config.templateId === tpl.id
                return (
                  <div
                    key={tpl.id}
                    onClick={() => handleTemplateSelect(tpl.id)}
                    className={`relative rounded-lg border overflow-hidden transition-all cursor-pointer ${
                      isSelected
                        ? 'border-[#00d9ff] shadow-lg shadow-[#00d9ff]/10'
                        : 'border-[#1e293b] hover:border-[#00d9ff]/30 card-hover'
                    }`}
                  >
                    {/* Template Preview */}
                    <div
                      className="h-36 relative flex items-center justify-center"
                      style={{
                        background: `linear-gradient(135deg, ${tpl.color}40, ${tpl.color}10)`,
                      }}
                    >
                      <Monitor
                        className="w-12 h-12"
                        style={{ color: tpl.color }}
                      />
                      {isSelected && (
                        <div className="absolute top-2 right-2 bg-[#00d9ff] rounded-full p-1">
                          <Check className="w-3 h-3 text-[#0a192f]" />
                        </div>
                      )}
                    </div>
                    <div className="p-4 bg-[#0a192f]">
                      <h4 className="text-white text-sm font-medium">
                        {tpl.name}
                      </h4>
                      <p className="text-xs text-[#8892a0] mt-1">
                        {tpl.desc}
                      </p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </TabsContent>

        {/* Tab 3: License Management */}
        <TabsContent value="license" className="space-y-6 mt-6">
          <div className="bg-[#112240] border border-[#1e293b] rounded-lg p-6 max-w-2xl space-y-6">
            <div className="flex items-center gap-3">
              <Shield className="w-5 h-5 text-[#8892a0]" />
              <h3 className="text-white font-medium">License管理</h3>
            </div>

            {/* Status */}
            <div
              className={`flex items-center gap-3 p-4 rounded-lg border ${
                license.isActive
                  ? 'bg-[#00ff88]/5 border-[#00ff88]/20'
                  : 'bg-[#ff9500]/5 border-[#ff9500]/20'
              }`}
            >
              <div
                className={`w-3 h-3 rounded-full ${
                  license.isActive ? 'bg-[#00ff88]' : 'bg-[#ff9500]'
                }`}
              />
              <span
                className={`text-sm font-medium ${
                  license.isActive ? 'text-[#00ff88]' : 'text-[#ff9500]'
                }`}
              >
                {license.isActive ? '已激活' : '未激活'}
              </span>
            </div>

            {/* Hardware Fingerprint */}
            <div className="grid gap-2">
              <Label className="text-[#8892a0]">硬件指纹</Label>
              <div className="flex gap-2">
                <Input
                  readOnly
                  value={license.hardwareFingerprint || '加载中...'}
                  className="bg-[#0a192f] border-[#1e293b] font-mono text-xs"
                />
                <Button
                  variant="outline"
                  size="sm"
                  className="border-[#1e293b] text-[#8892a0] hover:text-white hover:bg-[#172a45] flex-shrink-0"
                  onClick={handleCopyFingerprint}
                >
                  {copied ? (
                    <Check className="w-4 h-4 text-[#00ff88]" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </Button>
              </div>
            </div>

            {/* License Info */}
            {license.isActive && (
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-[#0a192f] border border-[#1e293b] rounded-lg p-4">
                  <p className="text-xs text-[#8892a0] mb-1">授权到期时间</p>
                  <p className="text-sm text-white font-medium">
                    {license.expiryDate || '永久'}
                  </p>
                </div>
                <div className="bg-[#0a192f] border border-[#1e293b] rounded-lg p-4">
                  <p className="text-xs text-[#8892a0] mb-1">最大设备数</p>
                  <p className="text-sm text-white font-medium">
                    {license.maxDevices} 台
                  </p>
                </div>
              </div>
            )}

            {/* Offline Activation */}
            <div className="grid gap-2">
              <Label className="text-[#8892a0]">离线激活</Label>
              <Textarea
                value={activationCode}
                onChange={(e) => setActivationCode(e.target.value)}
                placeholder="请粘贴激活码..."
                className="bg-[#0a192f] border-[#1e293b] min-h-[100px] font-mono text-xs"
              />
              <Button
                onClick={handleActivate}
                disabled={activating || !activationCode.trim()}
                className="bg-[#00d9ff] text-[#0a192f] hover:bg-[#00d9ff]/80 w-fit"
              >
                {activating ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Shield className="w-4 h-4 mr-2" />
                )}
                激活
              </Button>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
