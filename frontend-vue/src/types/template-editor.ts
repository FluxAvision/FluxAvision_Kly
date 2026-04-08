/**
 * 大屏模板编辑器类型定义
 */

/** 组件类型 */
export type ComponentType =
  | 'border'        // DataV 边框
  | 'decoration'    // DataV 装饰
  | 'metric-card'   // 指标卡片
  | 'counter'       // 数字计数器
  | 'chart-line'    // 折线图
  | 'chart-bar'     // 柱状图
  | 'video'         // 视频画面
  | 'title'         // 标题组件
  | 'text'          // 文本
  | 'clock'         // 实时时间

/** 数据源类型 */
export type DataSourceType = 'metric' | 'device' | 'hourly' | 'static'

/** 数据源配置 */
export interface DataSourceConfig {
  type: DataSourceType
  key?: string       // 指标 key 或设备 ID
  transform?: string // 数据转换函数
}

/** 组件样式配置 */
export interface ComponentStyles {
  backgroundColor?: string
  borderColor?: string
  borderWidth?: number
  borderRadius?: number
  color?: string
  fontSize?: number
  fontWeight?: string
  textAlign?: 'left' | 'center' | 'right'
  padding?: number
  boxShadow?: string
}

/** 组件配置 */
export interface ComponentConfig {
  id: string                    // 组件唯一 ID
  type: ComponentType           // 组件类型
  name: string                  // 组件名称
  x: number                     // X 坐标
  y: number                     // Y 坐标
  width: number                 // 宽度
  height: number                // 高度
  rotation: number              // 旋转角度
  opacity: number               // 透明度 0-1
  zIndex: number                // 层级
  locked: boolean               // 是否锁定
  visible: boolean              // 是否可见

  // 组件特定属性
  props: Record<string, any>    // 组件属性

  // 数据绑定
  dataSource?: DataSourceConfig

  // 样式配置
  styles?: ComponentStyles
}

/** 画布网格配置 */
export interface CanvasGridConfig {
  enabled: boolean
  size: number
  snapToGrid: boolean
}

/** 画布配置 */
export interface CanvasConfig {
  width: number
  height: number
  backgroundColor: string
  backgroundImage?: string
  grid: CanvasGridConfig
  fitToScreen?: boolean  // 是否平铺满屏
}

/** 模板配置 */
export interface TemplateConfig {
  version: string
  canvas: CanvasConfig
  components: ComponentConfig[]
}

/** 模板数据（来自后端） */
export interface ScreenTemplateData {
  id: string
  name: string
  description: string
  thumbnail: string
  layout: string
  templateConfig: string | TemplateConfig  // JSON 字符串或已解析对象
  canvasWidth: number
  canvasHeight: number
  backgroundColor: string
  backgroundImage: string
  isSystem: boolean
  isPublished: boolean
  createdAt: string
  updatedAt: string
}

/** 组件定义（用于组件面板） */
export interface ComponentDefinition {
  type: ComponentType
  name: string
  icon: string
  category: 'border' | 'metric' | 'chart' | 'video' | 'text'
  defaultProps: Record<string, any>
  defaultSize: { width: number; height: number }
}

/** 指标类型定义 */
export type MetricKey =
  | 'todayIn'
  | 'todayOut'
  | 'currentIn'
  | 'weekIn'
  | 'weekOut'
  | 'monthIn'
  | 'monthOut'
  | 'totalIn'
  | 'totalOut'

/** 指标配置 */
export interface MetricOption {
  key: MetricKey
  label: string
  color: string
}

/** 系统指标列表 */
export const METRIC_OPTIONS: MetricOption[] = [
  { key: 'todayIn', label: '今日进', color: '#00d9ff' },
  { key: 'todayOut', label: '今日出', color: '#00ff88' },
  { key: 'currentIn', label: '当前在场', color: '#4a9eff' },
  { key: 'weekIn', label: '本周进', color: '#ff9500' },
  { key: 'weekOut', label: '本周出', color: '#a855f7' },
  { key: 'monthIn', label: '本月进', color: '#f43f5e' },
  { key: 'monthOut', label: '本月出', color: '#f97316' },
  { key: 'totalIn', label: '累计进', color: '#06b6d4' },
  { key: 'totalOut', label: '累计出', color: '#10b981' },
]

/** 组件面板定义 */
export const COMPONENT_DEFINITIONS: ComponentDefinition[] = [
  // 边框装饰
  {
    type: 'border',
    name: '边框容器',
    icon: 'square',
    category: 'border',
    defaultProps: { borderType: 'dv-border-box-1' },
    defaultSize: { width: 400, height: 300 },
  },
  {
    type: 'decoration',
    name: '装饰线',
    icon: 'sparkles',
    category: 'border',
    defaultProps: { decorationType: 'dv-decoration-1' },
    defaultSize: { width: 200, height: 30 },
  },
  // 指标卡片
  {
    type: 'metric-card',
    name: '指标卡片',
    icon: 'credit-card',
    category: 'metric',
    defaultProps: { title: '指标名称', showIcon: true },
    defaultSize: { width: 280, height: 140 },
  },
  {
    type: 'counter',
    name: '数字计数器',
    icon: 'hash',
    category: 'metric',
    defaultProps: { title: '来访总人数', digits: 8 },
    defaultSize: { width: 500, height: 100 },
  },
  // 图表
  {
    type: 'chart-line',
    name: '折线图',
    icon: 'trending-up',
    category: 'chart',
    defaultProps: { title: '客流趋势', showIn: true, showOut: true, smooth: true, areaStyle: true },
    defaultSize: { width: 600, height: 350 },
  },
  {
    type: 'chart-bar',
    name: '柱状图',
    icon: 'bar-chart-2',
    category: 'chart',
    defaultProps: { title: '客流对比', showIn: true, showOut: true },
    defaultSize: { width: 600, height: 350 },
  },
  // 视频
  {
    type: 'video',
    name: '实时视频',
    icon: 'video',
    category: 'video',
    defaultProps: { showName: true, autoPlay: true },
    defaultSize: { width: 400, height: 300 },
  },
  // 文本
  {
    type: 'title',
    name: '标题',
    icon: 'type',
    category: 'text',
    defaultProps: { text: '大屏标题', level: 1 },
    defaultSize: { width: 300, height: 50 },
  },
  {
    type: 'text',
    name: '文本',
    icon: 'file-text',
    category: 'text',
    defaultProps: { text: '文本内容', fontSize: 14 },
    defaultSize: { width: 200, height: 30 },
  },
  // 时间
  {
    type: 'clock',
    name: '实时时间',
    icon: 'clock',
    category: 'text',
    defaultProps: { format: 'full', showDate: true, showWeek: true, showTime: true },
    defaultSize: { width: 400, height: 50 },
  },
]

/** 获取组件默认配置 */
export function getComponentDefault(type: ComponentType, name?: string): Omit<ComponentConfig, 'id' | 'x' | 'y'> {
  const def = COMPONENT_DEFINITIONS.find(d => d.type === type)
  if (!def) {
    return {
      type,
      name: name || type,
      width: 200,
      height: 100,
      rotation: 0,
      opacity: 1,
      zIndex: 1,
      locked: false,
      visible: true,
      props: {},
    }
  }

  const config: Omit<ComponentConfig, 'id' | 'x' | 'y'> = {
    type,
    name: name || def.name,
    width: def.defaultSize.width,
    height: def.defaultSize.height,
    rotation: 0,
    opacity: 1,
    zIndex: 1,
    locked: false,
    visible: true,
    props: { ...def.defaultProps },
  }

  // 为指标卡片设置默认数据源
  if (type === 'metric-card') {
    config.dataSource = { type: 'metric', key: 'todayIn' }
  }

  // 为数字计数器设置默认数据源
  if (type === 'counter') {
    config.dataSource = { type: 'metric', key: 'totalIn' }
  }

  // 为图表组件设置默认数据源
  if (type === 'chart-line' || type === 'chart-bar') {
    config.dataSource = { type: 'hourly' }
  }

  return config
}

/** 创建空模板配置 */
export function createEmptyTemplate(): TemplateConfig {
  return {
    version: '1.0',
    canvas: {
      width: 1920,
      height: 1080,
      backgroundColor: '#0a192f',
      grid: { enabled: true, size: 20, snapToGrid: true },
      fitToScreen: true,
    },
    components: [],
  }
}

/** 解析模板配置 */
export function parseTemplateConfig(config: string | TemplateConfig | undefined): TemplateConfig {
  if (!config) {
    return createEmptyTemplate()
  }
  if (typeof config === 'string') {
    try {
      const parsed = JSON.parse(config)
      return { ...createEmptyTemplate(), ...parsed }
    } catch {
      return createEmptyTemplate()
    }
  }
  return { ...createEmptyTemplate(), ...config }
}
