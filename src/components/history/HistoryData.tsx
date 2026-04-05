'use client'

import { useEffect, useState, useCallback } from 'react'
import { Download, Loader2, BarChart3, LineChart, Camera } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Cell,
} from 'recharts'

interface DailyData {
  date: string
  countIn: number
  countOut: number
}

interface DeviceDailyData {
  deviceId: string
  deviceName: string
  deviceLocation: string
  deviceStatus: string
  deviceIp: string
  countIn: number
  countOut: number
  currentInside: number
  percentage: number
}

interface DeviceOption {
  id: string
  name: string
}

export default function HistoryData() {
  const today = new Date()
  const defaultEndDate = today.toISOString().split('T')[0]
  const weekAgo = new Date(today)
  weekAgo.setDate(weekAgo.getDate() - 7)
  const defaultStartDate = weekAgo.toISOString().split('T')[0]

  const [startDate, setStartDate] = useState(defaultStartDate)
  const [endDate, setEndDate] = useState(defaultEndDate)
  const [selectedDevice, setSelectedDevice] = useState<string>('__all__')
  const [deviceOptions, setDeviceOptions] = useState<DeviceOption[]>([])
  const [data, setData] = useState<DailyData[]>([])
  const [deviceDailyData, setDeviceDailyData] = useState<DeviceDailyData[]>([])
  const [loading, setLoading] = useState(false)
  const [chartType, setChartType] = useState<'area' | 'bar'>('area')

  // 加载设备列表
  useEffect(() => {
    fetch('/api/devices')
      .then(res => res.ok ? res.json() : null)
      .then(json => {
        const list = json?.data || []
        setDeviceOptions(Array.isArray(list) ? list.map((d: any) => ({ id: d.id, name: d.name })) : [])
      })
      .catch(() => {})
  }, [])

  const fetchData = useCallback(async () => {
    if (!startDate || !endDate) return
    setLoading(true)
    try {
      const params = new URLSearchParams({ startDate, endDate })
      if (selectedDevice && selectedDevice !== '__all__') {
        params.set('deviceId', selectedDevice)
      }
      const res = await fetch(`/api/traffic/history?${params}`)
      if (res.ok) {
        const json = await res.json()
        const apiData = json.data || json
        setData(apiData.daily || [])
        // 单天门店汇总时, 有各设备分栏明细
        setDeviceDailyData(apiData.dailyDeviceData || [])
      }
    } catch {
      // Keep empty
    } finally {
      setLoading(false)
    }
  }, [startDate, endDate, selectedDevice])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleExportCSV = () => {
    if (data.length === 0) return

    const BOM = '\uFEFF'
    const deviceLabel = selectedDevice === '__all__' ? '门店汇总' : `设备${selectedDevice}`
    const headers = `日期,${deviceLabel}进入人数,${deviceLabel}出去人数\n`
    const rows = data
      .map((d) => `${d.date},${d.countIn},${d.countOut}`)
      .join('\n')
    const csv = BOM + headers + rows

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `客流数据_${startDate}_${endDate}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  const isSingleDay = startDate === endDate
  const isStoreView = selectedDevice === '__all__'

  const chartData = data.map((d) => ({
    ...d,
    date: d.date.slice(5), // MM-DD
  }))

  const DEVICE_COLORS = ['#00d9ff', '#00ff88', '#ff9500', '#a855f7', '#f43f5e', '#06b6d4', '#f97316', '#10b981']

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="bg-[#112240] border border-[#1e293b] rounded-lg p-4">
        <div className="flex items-end gap-4 flex-wrap">
          <div className="grid gap-2">
            <Label className="text-[#8892a0] text-xs">开始日期</Label>
            <Input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="bg-[#0a192f] border-[#1e293b] w-44"
            />
          </div>
          <div className="grid gap-2">
            <Label className="text-[#8892a0] text-xs">结束日期</Label>
            <Input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="bg-[#0a192f] border-[#1e293b] w-44"
            />
          </div>
          <div className="grid gap-2">
            <Label className="text-[#8892a0] text-xs">设备筛选</Label>
            <Select value={selectedDevice} onValueChange={setSelectedDevice}>
              <SelectTrigger className="bg-[#0a192f] border-[#1e293b] w-44">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">门店汇总 (全部设备)</SelectItem>
                {deviceOptions.map((d) => (
                  <SelectItem key={d.id} value={d.id}>{d.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex border border-[#1e293b] rounded-lg overflow-hidden">
            <button
              onClick={() => setChartType('area')}
              className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium transition-colors cursor-pointer ${
                chartType === 'area'
                  ? 'bg-[#00d9ff] text-[#0a192f]'
                  : 'bg-[#0a192f] text-[#8892a0] hover:text-white'
              }`}
            >
              <LineChart className="w-3.5 h-3.5" />
              趋势图
            </button>
            <button
              onClick={() => setChartType('bar')}
              className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium transition-colors cursor-pointer ${
                chartType === 'bar'
                  ? 'bg-[#00d9ff] text-[#0a192f]'
                  : 'bg-[#0a192f] text-[#8892a0] hover:text-white'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              柱状图
            </button>
          </div>
          <Button
            variant="outline"
            className="border-[#1e293b] text-[#8892a0] hover:text-white hover:bg-[#172a45]"
            onClick={handleExportCSV}
            disabled={data.length === 0 || loading}
          >
            <Download className="w-4 h-4 mr-2" />
            导出CSV
          </Button>
        </div>
        {/* 视图说明 */}
        <div className="mt-2">
          <span className="text-xs text-[#8892a0]">
            {isStoreView
              ? '当前查看: 门店汇总 (所有设备客流之和)'
              : `当前查看: 单设备 (${deviceOptions.find(d => d.id === selectedDevice)?.name || ''})`}
          </span>
        </div>
      </div>

      {/* Chart */}
      <div className="bg-[#112240] border border-[#1e293b] rounded-lg p-5">
        <h3 className="text-white font-medium mb-4">
          历史客流数据 {isStoreView ? '(门店汇总)' : '(单设备)'}
        </h3>
        {loading ? (
          <Skeleton className="h-[350px] w-full bg-[#1e293b]" />
        ) : data.length === 0 ? (
          <div className="flex items-center justify-center h-[350px] text-[#8892a0]">
            暂无数据
          </div>
        ) : chartType === 'area' ? (
          <ResponsiveContainer width="100%" height={350}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="histColorIn" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00d9ff" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#00d9ff" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="histColorOut" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00ff88" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#00ff88" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="date" stroke="#8892a0" tick={{ fontSize: 12 }} />
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
                fill="url(#histColorIn)"
                name="countIn"
              />
              <Area
                type="monotone"
                dataKey="countOut"
                stroke="#00ff88"
                fillOpacity={1}
                fill="url(#histColorOut)"
                name="countOut"
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="date" stroke="#8892a0" tick={{ fontSize: 12 }} />
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
              <Bar
                dataKey="countIn"
                fill="#00d9ff"
                radius={[4, 4, 0, 0]}
                name="countIn"
              />
              <Bar
                dataKey="countOut"
                fill="#00ff88"
                radius={[4, 4, 0, 0]}
                name="countOut"
              />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* 单天门店汇总: 各设备分栏明细 */}
      {!loading && isSingleDay && isStoreView && deviceDailyData.length > 0 && (
        <div className="bg-[#112240] border border-[#1e293b] rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-white font-medium">各设备客流分栏</h3>
            <span className="text-xs text-[#8892a0]">
              {deviceDailyData.length} 台设备贡献
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {deviceDailyData.map((dev, idx) => (
              <div
                key={dev.deviceId}
                className="bg-[#0a192f] border border-[#1e293b] rounded-lg p-4"
              >
                <div className="flex items-center gap-2 mb-3">
                  <Camera className="w-4 h-4" style={{ color: DEVICE_COLORS[idx % DEVICE_COLORS.length] }} />
                  <span className="text-sm text-white font-medium truncate">{dev.deviceName}</span>
                  <span className="text-xs text-[#8892a0] ml-auto">{dev.percentage}%</span>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <p className="text-[10px] text-[#8892a0]">进入</p>
                    <p className="text-sm font-bold text-[#00d9ff]">{dev.countIn}</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-[#8892a0]">出去</p>
                    <p className="text-sm font-bold text-[#00ff88]">{dev.countOut}</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-[#8892a0]">在场</p>
                    <p className="text-sm font-bold text-[#4a9eff]">{dev.currentInside}</p>
                  </div>
                </div>
                <div className="mt-2 h-1.5 bg-[#1e293b] rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${dev.percentage}%`,
                      backgroundColor: DEVICE_COLORS[idx % DEVICE_COLORS.length],
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Data Table Summary */}
      {!loading && data.length > 0 && (
        <div className="bg-[#112240] border border-[#1e293b] rounded-lg p-5">
          <h3 className="text-white font-medium mb-3">
            数据汇总 {isStoreView ? '(门店)' : '(单设备)'}
          </h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-[#0a192f] border border-[#1e293b] rounded-lg p-4 text-center">
              <p className="text-xs text-[#8892a0] mb-1">总进入</p>
              <p className="text-xl font-bold text-[#00d9ff]">
                {data.reduce((s, d) => s + d.countIn, 0).toLocaleString()}
              </p>
            </div>
            <div className="bg-[#0a192f] border border-[#1e293b] rounded-lg p-4 text-center">
              <p className="text-xs text-[#8892a0] mb-1">总出去</p>
              <p className="text-xl font-bold text-[#00ff88]">
                {data.reduce((s, d) => s + d.countOut, 0).toLocaleString()}
              </p>
            </div>
            <div className="bg-[#0a192f] border border-[#1e293b] rounded-lg p-4 text-center">
              <p className="text-xs text-[#8892a0] mb-1">日均进入</p>
              <p className="text-xl font-bold text-[#4a9eff]">
                {Math.round(
                  data.reduce((s, d) => s + d.countIn, 0) / data.length
                ).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
