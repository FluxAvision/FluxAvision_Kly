'use client'

import { useEffect, useState, useCallback } from 'react'
import {
  Plus,
  Search,
  Edit2,
  Trash2,
  Wifi,
  WifiOff,
  AlertTriangle,
  Loader2,
  Eye,
  Radio,
  RefreshCw,
  XCircle,
} from 'lucide-react'
import dynamic from 'next/dynamic'

// 动态导入视频播放器组件（避免 SSR 问题）
const RTSPVideoPlayer = dynamic(() => import('@/components/video/RTSPVideoPlayer'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center bg-black h-96">
      <div className="text-center">
        <Loader2 className="w-8 h-8 mx-auto text-[#00d9ff] animate-spin mb-2" />
        <p className="text-sm text-[#8892a0]">加载播放器...</p>
      </div>
    </div>
  ),
})
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

interface Device {
  id: string
  name: string
  ip: string
  serialNumber: string
  location: string
  model: string
  rtspPort: number
  sdkPort: number
  channel: number
  username: string
  password: string
  rtspUrl: string
  status: string
  collectorState?: string
  collectorStarted?: boolean
  collectorMessage?: string
}

interface SearchDevice {
  name: string
  ip: string
  model: string
  serialNumber: string
}

const emptyDevice: Omit<Device, 'id'> = {
  name: '',
  ip: '',
  serialNumber: '',
  location: '',
  model: '大华',
  rtspPort: 554,
  sdkPort: 37777,
  channel: 0,
  username: 'admin',
  password: '',
  rtspUrl: '',
  status: 'offline',
}

function generateRtspUrl(
  model: string,
  ip: string,
  port: number,
  username: string,
  password: string
): string {
  if (!ip) return ''
  const cred = password ? `${username}:${password}` : username
  if (model === '海康威视') {
    return `rtsp://${cred}@${ip}:${port}/Streaming/Channels/101`
  }
  if (model === '大华') {
    return `rtsp://${cred}@${ip}:${port}/cam/realmonitor?channel=1&subtype=0`
  }
  return `rtsp://${cred}@${ip}:${port}/stream1`
}

export default function DeviceManagement() {
  const [devices, setDevices] = useState<Device[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')

  // Dialog states
  const [addDialogOpen, setAddDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [searchDialogOpen, setSearchDialogOpen] = useState(false)
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false)
  const [previewDevice, setPreviewDevice] = useState<Device | null>(null)

  // Form state
  const [formData, setFormData] = useState(emptyDevice)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [saveMessage, setSaveMessage] = useState('')

  // Search device
  const [searchIpRange, setSearchIpRange] = useState('')
  const [searchingDevices, setSearchingDevices] = useState(false)
  const [searchResults, setSearchResults] = useState<SearchDevice[]>([])

  const fetchDevices = useCallback(async () => {
    try {
      const res = await fetch('/api/devices')
      if (res.ok) {
        const json = await res.json()
        const devicesData = json.data || json
        setDevices(Array.isArray(devicesData) ? devicesData : [])
      }
    } catch {
      // Keep empty
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchDevices()
    // 定时刷新采集状态
    const interval = setInterval(fetchDevices, 10000)
    return () => clearInterval(interval)
  }, [fetchDevices])

  const updateForm = (field: string, value: string | number) => {
    setFormData((prev) => {
      const updated = { ...prev, [field]: value }
      if (
        ['model', 'ip', 'rtspPort', 'username', 'password'].includes(field)
      ) {
        updated.rtspUrl = generateRtspUrl(
          updated.model,
          updated.ip,
          updated.rtspPort,
          updated.username,
          updated.password
        )
      }
      return updated
    })
  }

  const handleSave = async () => {
    if (!formData.name || !formData.ip) return
    setSaving(true)
    setSaveMessage('')
    try {
      if (editingId) {
        const res = await fetch(`/api/devices/${editingId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData),
        })
        if (res.ok) {
          setEditDialogOpen(false)
          fetchDevices()
        }
      } else {
        const res = await fetch('/api/devices', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData),
        })
        if (res.ok) {
          const json = await res.json()
          const msg = json.data?.collectorMessage || ''
          setSaveMessage(msg)
          setTimeout(() => {
            setAddDialogOpen(false)
            setSaveMessage('')
            fetchDevices()
          }, 2000)
        }
      }
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!deletingId) return
    try {
      const res = await fetch(`/api/devices/${deletingId}`, { method: 'DELETE' })
      if (res.ok) {
        setDeleteConfirmOpen(false)
        setDeletingId(null)
        fetchDevices()
      }
    } catch {
      // Ignore
    }
  }

  const handleSearchDevices = async () => {
    if (!searchIpRange) return
    setSearchingDevices(true)
    setSearchResults([])
    // Simulate search with delay
    await new Promise((resolve) => setTimeout(resolve, 1500))
    const baseIp = searchIpRange.split('.')[0]
    setSearchResults([
      {
        name: `摄像头-001`,
        ip: `${baseIp}.101`,
        model: '大华',
        serialNumber: `DH-${Date.now()}`,
      },
      {
        name: `摄像头-002`,
        ip: `${baseIp}.102`,
        model: '海康威视',
        serialNumber: `HK-${Date.now()}`,
      },
    ])
    setSearchingDevices(false)
  }

  const handleSelectSearchedDevice = (device: SearchDevice) => {
    setFormData({
      ...emptyDevice,
      name: device.name,
      ip: device.ip,
      model: device.model,
      serialNumber: device.serialNumber,
      rtspUrl: generateRtspUrl(device.model, device.ip, 554, 'admin', ''),
    })
    setSearchDialogOpen(false)
    setAddDialogOpen(true)
  }

  const filteredDevices = devices.filter(
    (d) =>
      d.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.ip.includes(searchQuery) ||
      d.location.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const statusIcon = (status: string) => {
    if (status === 'online')
      return <Wifi className="w-3.5 h-3.5 text-[#00ff88]" />
    if (status === 'warning')
      return <AlertTriangle className="w-3.5 h-3.5 text-[#ff9500]" />
    return <WifiOff className="w-3.5 h-3.5 text-[#ef4444]" />
  }

  const statusText = (status: string) => {
    if (status === 'online') return '在线'
    if (status === 'warning') return '告警'
    return '离线'
  }

  const statusVariant = (status: string) => {
    if (status === 'online')
      return 'bg-[#00ff88]/10 text-[#00ff88] border-[#00ff88]/20'
    if (status === 'warning')
      return 'bg-[#ff9500]/10 text-[#ff9500] border-[#ff9500]/20'
    return 'bg-[#ef4444]/10 text-[#ef4444] border-[#ef4444]/20'
  }

  // 采集状态显示
  const collectorStateBadge = (state?: string) => {
    if (!state || state === 'not_started') return null

    const config: Record<string, { icon: React.ReactNode; text: string; className: string }> = {
      connected: {
        icon: <Radio className="w-3 h-3" />,
        text: '采集中',
        className: 'bg-[#00ff88]/10 text-[#00ff88] border-[#00ff88]/20',
      },
      connecting: {
        icon: <Loader2 className="w-3 h-3 animate-spin" />,
        text: '连接中',
        className: 'bg-[#00d9ff]/10 text-[#00d9ff] border-[#00d9ff]/20',
      },
      reconnecting: {
        icon: <RefreshCw className="w-3 h-3 animate-spin" />,
        text: '重连中',
        className: 'bg-[#ff9500]/10 text-[#ff9500] border-[#ff9500]/20',
      },
      disconnected: {
        icon: <XCircle className="w-3 h-3" />,
        text: '已断线',
        className: 'bg-[#ef4444]/10 text-[#ef4444] border-[#ef4444]/20',
      },
      stopped: {
        icon: <XCircle className="w-3 h-3" />,
        text: '已停止',
        className: 'bg-[#8892a0]/10 text-[#8892a0] border-[#8892a0]/20',
      },
    }

    const cfg = config[state]
    if (!cfg) return null

    return (
      <Badge variant="outline" className={cfg.className}>
        {cfg.icon}
        <span className="ml-1 text-[10px]">{cfg.text}</span>
      </Badge>
    )
  }

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8892a0]" />
          <Input
            placeholder="搜索设备名称、IP、位置..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 bg-[#0a192f] border-[#1e293b]"
          />
        </div>
        <Button
          variant="outline"
          className="border-[#1e293b] text-[#8892a0] hover:text-white hover:bg-[#172a45]"
          onClick={() => {
            setSearchIpRange('')
            setSearchResults([])
            setSearchDialogOpen(true)
          }}
        >
          <Search className="w-4 h-4 mr-2" />
          搜索设备
        </Button>
        <Button
          className="bg-[#00d9ff] text-[#0a192f] hover:bg-[#00d9ff]/80"
          onClick={() => {
            setFormData(emptyDevice)
            setEditingId(null)
            setSaveMessage('')
            setAddDialogOpen(true)
          }}
        >
          <Plus className="w-4 h-4 mr-2" />
          添加设备
        </Button>
      </div>

      {/* Device Table */}
      <div className="bg-[#112240] border border-[#1e293b] rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="border-[#1e293b] hover:bg-transparent">
                <TableHead className="text-[#8892a0]">设备名称</TableHead>
                <TableHead className="text-[#8892a0]">IP地址</TableHead>
                <TableHead className="text-[#8892a0]">安装位置</TableHead>
                <TableHead className="text-[#8892a0]">型号</TableHead>
                <TableHead className="text-[#8892a0]">状态</TableHead>
                <TableHead className="text-[#8892a0]">采集</TableHead>
                <TableHead className="text-[#8892a0] text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <TableRow key={i} className="border-[#1e293b]">
                    {Array.from({ length: 7 }).map((_, j) => (
                      <TableCell key={j} className="border-[#1e293b]">
                        <Skeleton className="h-5 w-20 bg-[#1e293b]" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : filteredDevices.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={7}
                    className="text-center py-12 text-[#8892a0]"
                  >
                    {devices.length === 0
                      ? '暂无设备，请添加设备'
                      : '未找到匹配的设备'}
                  </TableCell>
                </TableRow>
              ) : (
                filteredDevices.map((device) => (
                  <TableRow
                    key={device.id}
                    className="border-[#1e293b] hover:bg-[#172a45]/50"
                  >
                    <TableCell className="text-white font-medium">
                      {device.name}
                    </TableCell>
                    <TableCell className="text-[#8892a0] font-mono text-sm">
                      {device.ip}
                    </TableCell>
                    <TableCell className="text-[#8892a0]">
                      {device.location}
                    </TableCell>
                    <TableCell className="text-[#8892a0]">
                      {device.model}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={statusVariant(device.status)}
                      >
                        {statusIcon(device.status)}
                        <span className="ml-1">{statusText(device.status)}</span>
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {device.model === '大华' ? (
                        collectorStateBadge(device.collectorState)
                      ) : (
                        <span className="text-xs text-[#8892a0]">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        {device.status === 'online' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-[#00d9ff] hover:text-[#00d9ff] hover:bg-[#00d9ff]/10"
                            onClick={() => {
                              setPreviewDevice(device)
                              setPreviewDialogOpen(true)
                            }}
                          >
                            <Eye className="w-4 h-4 mr-1" />
                            预览
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-[#8892a0] hover:text-white hover:bg-[#172a45]"
                          onClick={() => {
                            setFormData(device)
                            setEditingId(device.id)
                            setSaveMessage('')
                            setEditDialogOpen(true)
                          }}
                        >
                          <Edit2 className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-[#ef4444] hover:text-[#ef4444] hover:bg-[#ef4444]/10"
                          onClick={() => {
                            setDeletingId(device.id)
                            setDeleteConfirmOpen(true)
                          }}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* Add Device Dialog */}
      <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
        <DialogContent className="bg-[#112240] border-[#1e293b] max-w-lg max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white">添加设备</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label className="text-[#8892a0]">名称</Label>
              <Input
                value={formData.name}
                onChange={(e) => updateForm('name', e.target.value)}
                placeholder="请输入设备名称"
                className="bg-[#0a192f] border-[#1e293b]"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label className="text-[#8892a0]">IP地址</Label>
                <Input
                  value={formData.ip}
                  onChange={(e) => updateForm('ip', e.target.value)}
                  placeholder="192.168.1.100"
                  className="bg-[#0a192f] border-[#1e293b] font-mono"
                />
              </div>
              <div className="grid gap-2">
                <Label className="text-[#8892a0]">序列号</Label>
                <Input
                  value={formData.serialNumber}
                  onChange={(e) => updateForm('serialNumber', e.target.value)}
                  placeholder="设备序列号"
                  className="bg-[#0a192f] border-[#1e293b]"
                />
              </div>
            </div>
            <div className="grid gap-2">
              <Label className="text-[#8892a0]">安装位置</Label>
              <Input
                value={formData.location}
                onChange={(e) => updateForm('location', e.target.value)}
                placeholder="如：一楼入口"
                className="bg-[#0a192f] border-[#1e293b]"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label className="text-[#8892a0]">型号</Label>
                <Select
                  value={formData.model}
                  onValueChange={(v) => updateForm('model', v)}
                >
                  <SelectTrigger className="bg-[#0a192f] border-[#1e293b]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="大华">大华</SelectItem>
                    <SelectItem value="海康威视">海康威视</SelectItem>
                    <SelectItem value="通用">通用</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label className="text-[#8892a0]">RTSP端口</Label>
                <Input
                  type="number"
                  value={formData.rtspPort}
                  onChange={(e) => updateForm('rtspPort', Number(e.target.value))}
                  className="bg-[#0a192f] border-[#1e293b] font-mono"
                />
              </div>
            </div>
            {/* 大华SDK专用字段 */}
            {formData.model === '大华' && (
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label className="text-[#8892a0]">SDK端口</Label>
                  <Input
                    type="number"
                    value={formData.sdkPort}
                    onChange={(e) => updateForm('sdkPort', Number(e.target.value))}
                    placeholder="37777"
                    className="bg-[#0a192f] border-[#1e293b] font-mono"
                  />
                  <p className="text-[10px] text-[#8892a0]/60">大华默认 37777</p>
                </div>
                <div className="grid gap-2">
                  <Label className="text-[#8892a0]">客流通道号</Label>
                  <Input
                    type="number"
                    value={formData.channel}
                    onChange={(e) => updateForm('channel', Number(e.target.value))}
                    placeholder="0"
                    min={0}
                    className="bg-[#0a192f] border-[#1e293b] font-mono"
                  />
                  <p className="text-[10px] text-[#8892a0]/60">从0开始, 通常是0</p>
                </div>
              </div>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label className="text-[#8892a0]">用户名</Label>
                <Input
                  value={formData.username}
                  onChange={(e) => updateForm('username', e.target.value)}
                  className="bg-[#0a192f] border-[#1e293b]"
                />
              </div>
              <div className="grid gap-2">
                <Label className="text-[#8892a0]">密码</Label>
                <Input
                  type="password"
                  value={formData.password}
                  onChange={(e) => updateForm('password', e.target.value)}
                  className="bg-[#0a192f] border-[#1e293b]"
                />
              </div>
            </div>
            <div className="grid gap-2">
              <Label className="text-[#8892a0]">RTSP地址</Label>
              <Input
                value={formData.rtspUrl}
                onChange={(e) => updateForm('rtspUrl', e.target.value)}
                placeholder="自动生成"
                className="bg-[#0a192f] border-[#1e293b] font-mono text-xs"
              />
            </div>
            {saveMessage && (
              <div className="text-xs text-[#00ff88] bg-[#00ff88]/5 border border-[#00ff88]/20 rounded-md p-2">
                {saveMessage}
              </div>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="ghost"
              onClick={() => { setAddDialogOpen(false); setSaveMessage('') }}
              className="text-[#8892a0] hover:text-white"
            >
              取消
            </Button>
            <Button
              onClick={handleSave}
              disabled={saving || !formData.name || !formData.ip}
              className="bg-[#00d9ff] text-[#0a192f] hover:bg-[#00d9ff]/80"
            >
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              添加
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Device Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="bg-[#112240] border-[#1e293b] max-w-lg max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white">编辑设备</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label className="text-[#8892a0]">名称</Label>
              <Input
                value={formData.name}
                onChange={(e) => updateForm('name', e.target.value)}
                className="bg-[#0a192f] border-[#1e293b]"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label className="text-[#8892a0]">IP地址</Label>
                <Input
                  value={formData.ip}
                  onChange={(e) => updateForm('ip', e.target.value)}
                  className="bg-[#0a192f] border-[#1e293b] font-mono"
                />
              </div>
              <div className="grid gap-2">
                <Label className="text-[#8892a0]">序列号</Label>
                <Input
                  value={formData.serialNumber}
                  onChange={(e) => updateForm('serialNumber', e.target.value)}
                  className="bg-[#0a192f] border-[#1e293b]"
                />
              </div>
            </div>
            <div className="grid gap-2">
              <Label className="text-[#8892a0]">安装位置</Label>
              <Input
                value={formData.location}
                onChange={(e) => updateForm('location', e.target.value)}
                className="bg-[#0a192f] border-[#1e293b]"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label className="text-[#8892a0]">型号</Label>
                <Select
                  value={formData.model}
                  onValueChange={(v) => updateForm('model', v)}
                >
                  <SelectTrigger className="bg-[#0a192f] border-[#1e293b]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="大华">大华</SelectItem>
                    <SelectItem value="海康威视">海康威视</SelectItem>
                    <SelectItem value="通用">通用</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label className="text-[#8892a0]">RTSP端口</Label>
                <Input
                  type="number"
                  value={formData.rtspPort}
                  onChange={(e) =>
                    updateForm('rtspPort', Number(e.target.value))
                  }
                  className="bg-[#0a192f] border-[#1e293b] font-mono"
                />
              </div>
            </div>
            {/* 大华SDK专用字段 */}
            {formData.model === '大华' && (
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label className="text-[#8892a0]">SDK端口</Label>
                  <Input
                    type="number"
                    value={formData.sdkPort}
                    onChange={(e) => updateForm('sdkPort', Number(e.target.value))}
                    className="bg-[#0a192f] border-[#1e293b] font-mono"
                  />
                </div>
                <div className="grid gap-2">
                  <Label className="text-[#8892a0]">客流通道号</Label>
                  <Input
                    type="number"
                    value={formData.channel}
                    onChange={(e) => updateForm('channel', Number(e.target.value))}
                    min={0}
                    className="bg-[#0a192f] border-[#1e293b] font-mono"
                  />
                </div>
              </div>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label className="text-[#8892a0]">用户名</Label>
                <Input
                  value={formData.username}
                  onChange={(e) => updateForm('username', e.target.value)}
                  className="bg-[#0a192f] border-[#1e293b]"
                />
              </div>
              <div className="grid gap-2">
                <Label className="text-[#8892a0]">密码</Label>
                <Input
                  type="password"
                  value={formData.password}
                  onChange={(e) => updateForm('password', e.target.value)}
                  className="bg-[#0a192f] border-[#1e293b]"
                />
              </div>
            </div>
            <div className="grid gap-2">
              <Label className="text-[#8892a0]">RTSP地址</Label>
              <Input
                value={formData.rtspUrl}
                onChange={(e) => updateForm('rtspUrl', e.target.value)}
                className="bg-[#0a192f] border-[#1e293b] font-mono text-xs"
              />
            </div>
            {saveMessage && (
              <div className="text-xs text-[#00ff88] bg-[#00ff88]/5 border border-[#00ff88]/20 rounded-md p-2">
                {saveMessage}
              </div>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="ghost"
              onClick={() => { setEditDialogOpen(false); setSaveMessage('') }}
              className="text-[#8892a0] hover:text-white"
            >
              取消
            </Button>
            <Button
              onClick={handleSave}
              disabled={saving || !formData.name || !formData.ip}
              className="bg-[#00d9ff] text-[#0a192f] hover:bg-[#00d9ff]/80"
            >
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Search Device Dialog */}
      <Dialog open={searchDialogOpen} onOpenChange={setSearchDialogOpen}>
        <DialogContent className="bg-[#112240] border-[#1e293b] max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-white">搜索局域网设备</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid gap-2">
              <Label className="text-[#8892a0]">IP地址段</Label>
              <div className="flex gap-2">
                <Input
                  value={searchIpRange}
                  onChange={(e) => setSearchIpRange(e.target.value)}
                  placeholder="192.168.1"
                  className="bg-[#0a192f] border-[#1e293b] font-mono"
                />
                <Button
                  onClick={handleSearchDevices}
                  disabled={searchingDevices}
                  className="bg-[#00d9ff] text-[#0a192f] hover:bg-[#00d9ff]/80 flex-shrink-0"
                >
                  {searchingDevices && (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  )}
                  搜索
                </Button>
              </div>
            </div>
            {searchResults.length > 0 && (
              <div className="space-y-2">
                <Label className="text-[#8892a0]">
                  发现 {searchResults.length} 个设备
                </Label>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {searchResults.map((device, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between bg-[#0a192f] border border-[#1e293b] rounded-lg p-3 hover:border-[#00d9ff]/30 transition-colors"
                    >
                      <div>
                        <p className="text-sm text-white">{device.name}</p>
                        <p className="text-xs text-[#8892a0] font-mono">
                          {device.ip} · {device.model}
                        </p>
                      </div>
                      <Button
                        size="sm"
                        className="bg-[#00d9ff] text-[#0a192f] hover:bg-[#00d9ff]/80"
                        onClick={() => handleSelectSearchedDevice(device)}
                      >
                        选择
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Video Preview Dialog */}
      <Dialog open={previewDialogOpen} onOpenChange={(open) => {
        setPreviewDialogOpen(open)
        if (!open) setPreviewDevice(null)
      }}>
        <DialogContent className="bg-[#112240] border-[#1e293b] max-w-4xl w-full p-0 overflow-hidden">
          <DialogHeader className="px-5 pt-5 pb-3">
            <div className="flex items-center justify-between">
              <div>
                <DialogTitle className="text-white">
                  视频预览 - {previewDevice?.name || ''}
                </DialogTitle>
                <p className="text-xs text-[#8892a0] mt-1">
                  {previewDevice?.ip} · {previewDevice?.location}
                </p>
              </div>
              {previewDevice?.rtspUrl && (
                <p className="text-[10px] text-[#8892a0]/60 font-mono max-w-xs truncate">
                  {previewDevice.rtspUrl}
                </p>
              )}
            </div>
          </DialogHeader>
          <div className="relative bg-black" style={{ height: '70vh' }}>
            {previewDevice && (
              <RTSPVideoPlayer
                deviceId={previewDevice.id}
                name={previewDevice.name}
                status={previewDevice.status}
                autoPlay={true}
                showControls={true}
                compact={false}
                className="w-full h-full"
              />
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirm Dialog */}
      <Dialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <DialogContent className="bg-[#112240] border-[#1e293b] max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-white">确认删除</DialogTitle>
          </DialogHeader>
          <p className="text-[#8892a0] text-sm">
            确定要删除该设备吗？删除后将自动停止客流采集并清理相关数据，此操作不可撤销。
          </p>
          <DialogFooter>
            <Button
              variant="ghost"
              onClick={() => setDeleteConfirmOpen(false)}
              className="text-[#8892a0] hover:text-white"
            >
              取消
            </Button>
            <Button
              onClick={handleDelete}
              className="bg-[#ef4444] text-white hover:bg-[#ef4444]/80"
            >
              删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
