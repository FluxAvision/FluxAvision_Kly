import { ref, onMounted, onUnmounted, markRaw } from 'vue'
import {
  LogIn, LogOut, Users, TrendingUp, TrendingDown, CalendarDays, Hash,
} from 'lucide-vue-next'

export interface LargeScreenConfig {
  title: string
  subtitle: string
  backgroundImage: string
  metrics: string[]
  deviceIds: string[]
  templateId: string
}

export interface HourlyData {
  hour: string
  countIn: number
  countOut: number
}

export interface Device {
  id: string
  name: string
  ip: string
  status: string
}

export const metricMap: Record<string, { label: string; icon: any; color: string }> = {
  todayIn: { label: '今日进', icon: markRaw(LogIn), color: '#00d9ff' },
  todayOut: { label: '今日出', icon: markRaw(LogOut), color: '#00ff88' },
  currentIn: { label: '当前在场', icon: markRaw(Users), color: '#4a9eff' },
  weekIn: { label: '本周进', icon: markRaw(TrendingUp), color: '#ff9500' },
  weekOut: { label: '本周出', icon: markRaw(TrendingDown), color: '#a855f7' },
  monthIn: { label: '本月进', icon: markRaw(CalendarDays), color: '#f43f5e' },
  monthOut: { label: '本月出', icon: markRaw(CalendarDays), color: '#f97316' },
  totalIn: { label: '累计进', icon: markRaw(Hash), color: '#06b6d4' },
  totalOut: { label: '累计出', icon: markRaw(Hash), color: '#10b981' },
}

export function useLargeScreenData() {
  const storeLogo = ref('')
  const customLabels = ref<Record<string, string>>({})

  const config = ref<LargeScreenConfig>({
    title: '客流统计大屏',
    subtitle: '实时客流数据展示',
    backgroundImage: '',
    metrics: ['todayIn', 'todayOut', 'currentIn'],
    deviceIds: [],
    templateId: '',
  })

  const metrics = ref<Record<string, number>>({
    todayIn: 0, todayOut: 0, currentIn: 0, weekIn: 0, weekOut: 0,
    monthIn: 0, monthOut: 0, totalIn: 0, totalOut: 0,
  })

  function getLabel(key: string): string {
    return customLabels.value[key] || metricMap[key]?.label || key
  }

  const hourlyData = ref<HourlyData[]>([])
  const devices = ref<Device[]>([])
  const allDevices = ref<Device[]>([])  // 所有设备，用于自定义模板
  const loading = ref(true)
  let interval: ReturnType<typeof setInterval> | null = null

  // 实时时钟
  const clockTime = ref('')
  let clockInterval: ReturnType<typeof setInterval> | null = null
  function updateClock() {
    const now = new Date()
    const weekDays = ['日', '一', '二', '三', '四', '五', '六']
    const y = now.getFullYear()
    const m = now.getMonth() + 1
    const d = now.getDate()
    const h = String(now.getHours()).padStart(2, '0')
    const mi = String(now.getMinutes()).padStart(2, '0')
    const s = String(now.getSeconds()).padStart(2, '0')
    const w = weekDays[now.getDay()]
    clockTime.value = `${y}年${m}月${d}日${h}点${mi}分${s}秒  星期${w}`
  }

  async function fetchData() {
    try {
      const [screenRes, dashRes, devRes, settingsRes] = await Promise.all([
        fetch('/api/large-screen'),
        fetch('/api/traffic/dashboard'),
        fetch('/api/devices'),
        fetch('/api/settings'),
      ])

      if (screenRes.ok) {
        const json = await screenRes.json()
        const screenData = json.data || json
        config.value = {
          title: screenData.title || '客流统计大屏',
          subtitle: screenData.subtitle || '实时客流数据展示',
          backgroundImage: screenData.backgroundImage || '',
          metrics: screenData.metrics ? screenData.metrics.split(',') : ['todayIn', 'todayOut', 'currentIn'],
          deviceIds: screenData.deviceIds ? screenData.deviceIds.split(',').filter(Boolean) : [],
          templateId: screenData.templateId || '',
        }
      }
      if (dashRes.ok) {
        const json = await dashRes.json()
        const dashData = json.data || json
        const st = dashData.storeTotal || {}
        metrics.value = {
          todayIn: st.todayIn || dashData.todayIn || 0,
          todayOut: st.todayOut || dashData.todayOut || 0,
          currentIn: st.currentIn || dashData.currentIn || 0,
          weekIn: st.weekIn || dashData.weekIn || 0,
          weekOut: st.weekOut || dashData.weekOut || 0,
          monthIn: st.monthIn || dashData.monthIn || 0,
          monthOut: st.monthOut || dashData.monthOut || 0,
          totalIn: st.totalIn || dashData.totalIn || 0,
          totalOut: st.totalOut || dashData.totalOut || 0,
        }
        hourlyData.value = (dashData.hourlyToday || []).map((h: any) => ({
          ...h,
          hour: `${String(h.hour).padStart(2, '0')}:00`,
        }))
      }
      if (devRes.ok) {
        const json = await devRes.json()
        const deviceList: Device[] = Array.isArray(json.data) ? json.data : (Array.isArray(json) ? json : [])
        allDevices.value = deviceList  // 保存所有设备
        const effectiveIds = config.value.deviceIds.length > 0
          ? config.value.deviceIds
          : deviceList.filter(d => d.status === 'online').slice(0, 4).map(d => d.id)
        devices.value = deviceList.filter((d) => effectiveIds.includes(d.id))
      }
      if (settingsRes.ok) {
        const json = await settingsRes.json()
        const data = json.data || json
        if (data.storeLogo) storeLogo.value = data.storeLogo
        if (data.dashboardMetricsLabels) {
          try { customLabels.value = JSON.parse(data.dashboardMetricsLabels) } catch { customLabels.value = {} }
        }
      }
    } catch {
      // Keep defaults
    } finally {
      loading.value = false
    }
  }

  onMounted(() => {
    fetchData()
    interval = setInterval(fetchData, 10000)
    updateClock()
    clockInterval = setInterval(updateClock, 1000)
  })

  onUnmounted(() => {
    if (interval) clearInterval(interval)
    if (clockInterval) clearInterval(clockInterval)
  })

  return {
    config,
    metrics,
    hourlyData,
    devices,
    allDevices,
    storeLogo,
    customLabels,
    loading,
    clockTime,
    getLabel,
    fetchData,
  }
}
