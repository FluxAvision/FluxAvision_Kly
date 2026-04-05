'use client'

import { useEffect, useState } from 'react'
import {
  LogIn,
  LogOut,
  Users,
  TrendingUp,
  TrendingDown,
  Camera,
  CalendarDays,
  Hash,
} from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'

interface MetricCardProps {
  label: string
  value: number
  icon: React.ReactNode
  bgColor: string
  loading?: boolean
}

function MetricCard({ label, value, icon, bgColor, loading }: MetricCardProps) {
  return (
    <div className="metric-card p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-[#8892a0] mb-1">{label}</p>
          {loading ? (
            <Skeleton className="h-8 w-24 bg-[#1e293b]" />
          ) : (
            <p className="text-2xl font-bold text-white animate-count-up">
              {value.toLocaleString()}
            </p>
          )}
        </div>
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: bgColor }}
        >
          {icon}
        </div>
      </div>
    </div>
  )
}

interface HourlyData {
  hour: number
  countIn: number
  countOut: number
}

interface DeviceStatus {
  id: string
  name: string
  location: string
  status: string
  ip: string
  model: string
}

interface DashboardApiData {
  todayIn: number
  todayOut: number
  currentIn: number
  weekIn: number
  weekOut: number
  monthIn: number
  monthOut: number
  totalIn: number
  totalOut: number
  hourlyToday: HourlyData[]
  devices: DeviceStatus[]
}

interface DashboardProps {
  dashboardMetrics?: string
}

const metricConfig: Record<string, {
  label: string
  icon: React.ReactNode
  bgColor: string
}> = {
  todayIn: { label: '今日进', icon: <LogIn className="w-5 h-5 text-[#00d9ff]" />, bgColor: 'rgba(0, 217, 255, 0.1)' },
  todayOut: { label: '今日出', icon: <LogOut className="w-5 h-5 text-[#00ff88]" />, bgColor: 'rgba(0, 255, 136, 0.1)' },
  currentIn: { label: '当前在场', icon: <Users className="w-5 h-5 text-[#4a9eff]" />, bgColor: 'rgba(74, 158, 255, 0.1)' },
  weekIn: { label: '本周进', icon: <TrendingUp className="w-5 h-5 text-[#ff9500]" />, bgColor: 'rgba(255, 149, 0, 0.1)' },
  weekOut: { label: '本周出', icon: <TrendingDown className="w-5 h-5 text-[#a855f7]" />, bgColor: 'rgba(168, 85, 247, 0.1)' },
  monthIn: { label: '本月进', icon: <CalendarDays className="w-5 h-5 text-[#f43f5e]" />, bgColor: 'rgba(244, 63, 94, 0.1)' },
  monthOut: { label: '本月出', icon: <CalendarDays className="w-5 h-5 text-[#f97316]" />, bgColor: 'rgba(249, 115, 22, 0.1)' },
  totalIn: { label: '累计进人数', icon: <Hash className="w-5 h-5 text-[#06b6d4]" />, bgColor: 'rgba(6, 182, 212, 0.1)' },
  totalOut: { label: '累计出人数', icon: <Hash className="w-5 h-5 text-[#10b981]" />, bgColor: 'rgba(16, 185, 129, 0.1)' },
}

const defaultHourlyData = Array.from({ length: 24 }, (_, i) => ({
  hour: i,
  countIn: 0,
  countOut: 0,
}))

export default function Dashboard({ dashboardMetrics }: DashboardProps) {
  const [data, setData] = useState<DashboardApiData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await fetch('/api/traffic/dashboard')
        if (res.ok) {
          const json = await res.json()
          const apiData: DashboardApiData = json.data || json
          setData(apiData)
        }
      } catch {
        // Keep null
      } finally {
        setLoading(false)
      }
    }
    fetchData()

    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  const metrics = dashboardMetrics ? dashboardMetrics.split(',') : ['todayIn', 'todayOut', 'currentIn', 'weekIn']
  const hourlyData = data?.hourlyToday?.map(h => ({ ...h, hour: `${h.hour}:00` })) || defaultHourlyData.map(h => ({ ...h, hour: `${h.hour}:00` }))
  const devices = data?.devices || []

  return (
    <div className="space-y-6">
      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((key) => {
          const config = metricConfig[key]
          if (!config) return null
          const value = data ? (data as any)[key] || 0 : 0
          return (
            <MetricCard
              key={key}
              label={config.label}
              value={value}
              icon={config.icon}
              bgColor={config.bgColor}
              loading={loading}
            />
          )
        })}
      </div>

      {/* Hourly Trend Chart */}
      <div className="bg-[#112240] border border-[#1e293b] rounded-lg p-5">
        <h3 className="text-white font-medium mb-4">今日客流趋势</h3>
        {loading ? (
          <Skeleton className="h-[300px] w-full bg-[#1e293b]" />
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={hourlyData}>
              <defs>
                <linearGradient id="colorIn" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00d9ff" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#00d9ff" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorOut" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00ff88" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#00ff88" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis
                dataKey="hour"
                stroke="#8892a0"
                tick={{ fontSize: 12 }}
                interval={2}
              />
              <YAxis stroke="#8892a0" tick={{ fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#172a45',
                  border: '1px solid #1e293b',
                  borderRadius: '8px',
                  color: '#ffffff',
                }}
                formatter={(value: number, name: string) => [
                  value.toLocaleString(),
                  name === 'countIn' ? '进入' : '出去',
                ]}
              />
              <Legend
                formatter={(value: string) =>
                  value === 'countIn' ? '进入' : '出去'
                }
                wrapperStyle={{ color: '#8892a0' }}
              />
              <Area
                type="monotone"
                dataKey="countIn"
                stroke="#00d9ff"
                fillOpacity={1}
                fill="url(#colorIn)"
                name="countIn"
              />
              <Area
                type="monotone"
                dataKey="countOut"
                stroke="#00ff88"
                fillOpacity={1}
                fill="url(#colorOut)"
                name="countOut"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Device Status */}
      <div className="bg-[#112240] border border-[#1e293b] rounded-lg p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white font-medium">设备状态</h3>
          <span className="text-xs text-[#8892a0]">
            共 {devices.length} 台设备 · 在线 {devices.filter(d => d.status === 'online').length} 台
          </span>
        </div>
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {[1, 2, 3].map((i) => (
              <Skeleton
                key={i}
                className="h-20 w-full bg-[#1e293b] rounded-lg"
              />
            ))}
          </div>
        ) : devices.length === 0 ? (
          <div className="text-center py-12 text-[#8892a0]">
            <Camera className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="text-sm mb-1">暂无设备</p>
            <p className="text-xs opacity-60">请前往「设备管理」页面添加摄像头设备</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {devices.map((device) => (
              <div
                key={device.id}
                className="flex items-center gap-3 bg-[#0a192f] border border-[#1e293b] rounded-lg p-4 card-hover"
              >
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                  device.status === 'online'
                    ? 'bg-[#00ff88]/10'
                    : device.status === 'warning'
                      ? 'bg-[#ff9500]/10'
                      : 'bg-[#ef4444]/10'
                }`}>
                  <Camera className={`w-5 h-5 flex-shrink-0 ${
                    device.status === 'online'
                      ? 'text-[#00ff88]'
                      : device.status === 'warning'
                        ? 'text-[#ff9500]'
                        : 'text-[#ef4444]'
                  }`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white font-medium truncate">
                    {device.name}
                  </p>
                  <p className="text-xs text-[#8892a0] truncate">
                    {device.location} · {device.ip}
                  </p>
                </div>
                <div className="flex items-center gap-1.5 flex-shrink-0">
                  <div
                    className={`w-2 h-2 rounded-full ${
                      device.status === 'online'
                        ? 'bg-[#00ff88] animate-pulse-green'
                        : device.status === 'warning'
                          ? 'bg-[#ff9500]'
                          : 'bg-[#ef4444]'
                    }`}
                  />
                  <span
                    className={`text-xs font-medium ${
                      device.status === 'online'
                        ? 'text-[#00ff88]'
                        : device.status === 'warning'
                          ? 'text-[#ff9500]'
                          : 'text-[#ef4444]'
                    }`}
                  >
                    {device.status === 'online'
                      ? '在线'
                      : device.status === 'warning'
                        ? '告警'
                        : '离线'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
