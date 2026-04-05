'use client'

import { useEffect, useState, useCallback } from 'react'
import { X, LogIn, LogOut, Users, TrendingUp, TrendingDown, CalendarDays, Hash, Video, Wifi, WifiOff } from 'lucide-react'
import dynamic from 'next/dynamic'

// 动态导入视频播放器组件（避免 SSR 问题）
const RTSPVideoPlayer = dynamic(() => import('@/components/video/RTSPVideoPlayer'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center bg-black/40 h-full">
      <div className="text-center">
        <div className="w-8 h-8 mx-auto border-2 border-[#00d9ff]/30 border-t-[#00d9ff] rounded-full animate-spin mb-2" />
        <p className="text-xs text-[#8892a0]">加载播放器...</p>
      </div>
    </div>
  ),
})
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

interface LargeScreenConfig {
  title: string
  subtitle: string
  logo: string
  backgroundImage: string
  metrics: string[]
  deviceIds: string[]
  templateId: string
}

interface HourlyData {
  hour: string
  countIn: number
  countOut: number
}

interface Device {
  id: string
  name: string
  ip: string
  status: string
}

interface LargeScreenProps {
  onClose: () => void
}

const metricMap: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  todayIn: {
    label: '今日进',
    icon: <LogIn className="w-6 h-6" />,
    color: '#00d9ff',
  },
  todayOut: {
    label: '今日出',
    icon: <LogOut className="w-6 h-6" />,
    color: '#00ff88',
  },
  currentIn: {
    label: '当前在场',
    icon: <Users className="w-6 h-6" />,
    color: '#4a9eff',
  },
  weekIn: {
    label: '本周进',
    icon: <TrendingUp className="w-6 h-6" />,
    color: '#ff9500',
  },
  weekOut: {
    label: '本周出',
    icon: <TrendingDown className="w-6 h-6" />,
    color: '#a855f7',
  },
  monthIn: {
    label: '本月进',
    icon: <CalendarDays className="w-6 h-6" />,
    color: '#f43f5e',
  },
  monthOut: {
    label: '本月出',
    icon: <CalendarDays className="w-6 h-6" />,
    color: '#f97316',
  },
  totalIn: {
    label: '累计进',
    icon: <Hash className="w-6 h-6" />,
    color: '#06b6d4',
  },
  totalOut: {
    label: '累计出',
    icon: <Hash className="w-6 h-6" />,
    color: '#10b981',
  },
}

const templateGradients: Record<string, string> = {
  'tpl-blue': 'linear-gradient(135deg, #0a192f 0%, #1e3a5f 50%, #0a192f 100%)',
  'tpl-tech':
    'linear-gradient(135deg, #0a192f 0%, #0a2540 30%, #0d1b30 60%, #0a192f 100%)',
  'tpl-minimal': 'linear-gradient(135deg, #0a192f 0%, #112240 100%)',
  'tpl-data': 'linear-gradient(135deg, #0a192f 0%, #0f2a1f 50%, #0a192f 100%)',
}

export default function LargeScreenView({ onClose }: LargeScreenProps) {
  const [config, setConfig] = useState<LargeScreenConfig>({
    title: '客流统计大屏',
    subtitle: '实时客流数据展示',
    logo: '',
    backgroundImage: '',
    metrics: ['todayIn', 'todayOut', 'currentIn'],
    deviceIds: [],
    templateId: '',
  })
  const [metrics, setMetrics] = useState<Record<string, number>>({
    todayIn: 0,
    todayOut: 0,
    currentIn: 0,
    weekIn: 0,
    weekOut: 0,
    monthIn: 0,
    monthOut: 0,
    totalIn: 0,
    totalOut: 0,
  })
  const [hourlyData, setHourlyData] = useState<HourlyData[]>([])
  const [devices, setDevices] = useState<Device[]>([])
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    try {
      const [screenRes, dashRes, devRes] = await Promise.all([
        fetch('/api/large-screen'),
        fetch('/api/traffic/dashboard'),
        fetch('/api/devices'),
      ])

      if (screenRes.ok) {
        const json = await screenRes.json()
        const screenData = json.data || json
        setConfig({
          title: screenData.title || '客流统计大屏',
          subtitle: screenData.subtitle || '实时客流数据展示',
          logo: screenData.logo || '',
          backgroundImage: screenData.backgroundImage || '',
          metrics: screenData.metrics ? screenData.metrics.split(',') : ['todayIn', 'todayOut', 'currentIn'],
          deviceIds: screenData.deviceIds ? screenData.deviceIds.split(',').filter(Boolean) : [],
          templateId: screenData.templateId || '',
        })
      }
      if (dashRes.ok) {
        const json = await dashRes.json()
        const dashData = json.data || json
        setMetrics({
          todayIn: dashData.todayIn || 0,
          todayOut: dashData.todayOut || 0,
          currentIn: dashData.currentIn || 0,
          weekIn: dashData.weekIn || 0,
          weekOut: dashData.weekOut || 0,
          monthIn: dashData.monthIn || 0,
          monthOut: dashData.monthOut || 0,
          totalIn: dashData.totalIn || 0,
          totalOut: dashData.totalOut || 0,
        })
        setHourlyData(
          (dashData.hourlyToday || []).map((h: any) => ({
            ...h,
            hour: `${h.hour}:00`,
          }))
        )
      }
      if (devRes.ok) {
        const json = await devRes.json()
        const allDevices: Device[] = Array.isArray(json.data) ? json.data : (Array.isArray(json) ? json : [])
        const selectedIds = (json.data ? (json.data as any).deviceIds : null) || config.deviceIds
        const effectiveIds = selectedIds.length > 0
          ? selectedIds
          : allDevices.filter(d => d.status === 'online').slice(0, 4).map(d => d.id)
        const filtered = allDevices.filter((d) => effectiveIds.includes(d.id))
        setDevices(filtered)
      }
    } catch {
      // Keep defaults
    } finally {
      setLoading(false)
    }
  }, [config.deviceIds])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 15000)
    return () => clearInterval(interval)
  }, [fetchData])

  const bgStyle: React.CSSProperties = config.backgroundImage
    ? {
        backgroundImage: `url(${config.backgroundImage})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }
    : {
        background: templateGradients[config.templateId] || templateGradients['tpl-blue'],
      }

  return (
    <div className="fixed inset-0 z-[100] overflow-hidden" style={bgStyle}>
      {/* Overlay for readability */}
      <div className="absolute inset-0 bg-black/30" />

      {/* Content */}
      <div className="relative z-10 h-full flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <div className="flex items-center gap-4">
            {config.logo && (
              <img src={config.logo} alt="Logo" className="h-10 w-10 object-contain" />
            )}
            <div>
              <h1 className="text-2xl font-bold text-white glow-text-cyan">
                {config.title}
              </h1>
              <p className="text-sm text-[#8892a0]">{config.subtitle}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-10 h-10 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex gap-4 p-4 min-h-0">
          {/* Left: Metrics */}
          <div className="w-64 flex-shrink-0 flex flex-col gap-4">
            {config.metrics.map((key) => {
              const m = metricMap[key]
              if (!m) return null
              return (
                <div
                  key={key}
                  className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-5"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-[#8892a0]">{m.label}</span>
                    <div style={{ color: m.color }}>{m.icon}</div>
                  </div>
                  <p
                    className="text-3xl font-bold animate-count-up"
                    style={{ color: m.color }}
                  >
                    {loading ? '...' : (metrics as any)[key]?.toLocaleString() || 0}
                  </p>
                </div>
              )
            })}
          </div>

          {/* Center/Right: Video Grid + Chart */}
          <div className="flex-1 flex flex-col gap-4 min-w-0">
            {/* Video Grid */}
            <div className="flex-1 grid gap-4 min-h-0" style={{
              gridTemplateColumns: devices.length > 1 ? 'repeat(2, 1fr)' : '1fr',
              gridTemplateRows: devices.length > 2 ? 'repeat(2, 1fr)' : '1fr',
            }}>
              {devices.length === 0 && !loading ? (
                <div className="col-span-2 flex items-center justify-center text-[#8892a0]">
                  <div className="text-center">
                    <Video className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">暂无视频设备</p>
                  </div>
                </div>
              ) : (
                devices.map((device) => (
                  <div
                    key={device.id}
                    className="bg-black/40 border border-white/10 rounded-lg flex flex-col overflow-hidden"
                  >
                    <div className="flex items-center justify-between px-3 py-2 bg-black/30 flex-shrink-0">
                      <div className="flex items-center gap-2">
                        {device.status === 'online' ? (
                          <Wifi className="w-3.5 h-3.5 text-[#00ff88]" />
                        ) : (
                          <WifiOff className="w-3.5 h-3.5 text-[#ef4444]" />
                        )}
                        <span className="text-xs text-white">{device.name}</span>
                      </div>
                      <span className="text-xs text-[#8892a0] font-mono">{device.ip}</span>
                    </div>
                    <div className="flex-1 min-h-0">
                      <RTSPVideoPlayer
                        deviceId={device.id}
                        name={device.name}
                        status={device.status}
                        autoPlay={true}
                        compact={true}
                        showControls={true}
                        className="w-full h-full"
                      />
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Bottom Chart */}
            <div className="h-48 flex-shrink-0 bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-4">
              <h3 className="text-sm text-[#8892a0] mb-2">今日客流趋势</h3>
              <ResponsiveContainer width="100%" height="80%">
                <AreaChart data={hourlyData}>
                  <defs>
                    <linearGradient id="lsColorIn" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00d9ff" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#00d9ff" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="lsColorOut" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00ff88" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#00ff88" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis
                    dataKey="hour"
                    stroke="#8892a0"
                    tick={{ fontSize: 10 }}
                    interval={3}
                  />
                  <YAxis stroke="#8892a0" tick={{ fontSize: 10 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(23, 42, 69, 0.9)',
                      border: '1px solid #1e293b',
                      borderRadius: '8px',
                      color: '#ffffff',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="countIn"
                    stroke="#00d9ff"
                    fillOpacity={1}
                    fill="url(#lsColorIn)"
                  />
                  <Area
                    type="monotone"
                    dataKey="countOut"
                    stroke="#00ff88"
                    fillOpacity={1}
                    fill="url(#lsColorOut)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
