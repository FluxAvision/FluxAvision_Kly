/**
 * 设计器状态管理
 *
 * 使用 reactive/ref 管理设计器核心状态：
 * - templateConfig: 当前正在编辑的模板配置
 * - selectedComponentId: 当前选中的组件 ID
 * - zoom: 画布缩放百分比
 * - history/historyIndex: 撤销/重做历史记录
 */
import { ref, computed } from 'vue'
import {
  createEmptyTemplate,
  getComponentDefault,
  type TemplateConfig,
  type ComponentConfig,
  type ComponentType,
  type ComponentStyles,
  type DataSourceConfig,
  type AnimationConfig,
  type CanvasConfig,
} from '@/types/template-editor'

/** 生成唯一 ID */
function generateId(): string {
  return 'comp_' + Date.now() + '_' + Math.random().toString(36).substring(2, 8)
}

export function useDesignerState() {
  /** 当前编辑的模板配置 */
  const templateConfig = ref<TemplateConfig>(createEmptyTemplate())

  /** 当前选中的组件 ID */
  const selectedComponentId = ref<string | null>(null)

  /** 当前选中的组件（computed） */
  const selectedComponent = computed<ComponentConfig | null>(() => {
    if (!selectedComponentId.value) return null
    return templateConfig.value.components.find(c => c.id === selectedComponentId.value) ?? null
  })

  /** 画布缩放百分比 */
  const zoom = ref(100)

  /** 撤销历史 */
  const history = ref<TemplateConfig[]>([])

  /** 当前历史索引 */
  const historyIndex = ref(-1)

  /** 是否可以撤销 */
  const canUndo = computed(() => historyIndex.value > 0)

  /** 是否可以重做 */
  const canRedo = computed(() => historyIndex.value < history.value.length - 1)

  /** 组件数量 */
  const componentCount = computed(() => templateConfig.value.components.length)

  /** 画布网格配置 */
  const gridConfig = computed(() => templateConfig.value.canvas.grid)

  /** 保存当前状态到历史（用于撤销） */
  function pushHistory() {
    const snapshot = JSON.parse(JSON.stringify(templateConfig.value)) as TemplateConfig
    // 如果当前不在历史末尾，截断
    if (historyIndex.value < history.value.length - 1) {
      history.value = history.value.slice(0, historyIndex.value + 1)
    }
    history.value.push(snapshot)
    // 限制历史长度
    if (history.value.length > 50) {
      history.value.shift()
    } else {
      historyIndex.value++
    }
  }

  /** 撤销 */
  function undo() {
    if (!canUndo.value) return
    historyIndex.value--
    templateConfig.value = JSON.parse(JSON.stringify(history.value[historyIndex.value])) as TemplateConfig
    // 选中状态重置
    selectedComponentId.value = null
  }

  /** 重做 */
  function redo() {
    if (!canRedo.value) return
    historyIndex.value++
    templateConfig.value = JSON.parse(JSON.stringify(history.value[historyIndex.value])) as TemplateConfig
    // 选中状态重置
    selectedComponentId.value = null
  }

  /** 选中组件 */
  function selectComponent(id: string | null) {
    selectedComponentId.value = id
  }

  /** 设置缩放 */
  function setZoom(value: number) {
    zoom.value = Math.max(25, Math.min(500, value))
  }

  /** 网格吸附 */
  function snapToGrid(value: number, gridSize: number): number {
    if (gridSize <= 0) return value
    return Math.round(value / gridSize) * gridSize
  }

  /** 模板编辑模式 */
  const templateEditMode = ref(false)

  /** 切换模板编辑模式 */
  function toggleTemplateEditMode() {
    templateEditMode.value = !templateEditMode.value
    if (templateEditMode.value) {
      // 进入模板编辑模式时取消选中组件
      selectedComponentId.value = null
    }
  }

  /** 通用更新组件属性（不记录历史，用于属性面板实时编辑） */
  function updateComponent(id: string, updates: Partial<ComponentConfig>) {
    const idx = templateConfig.value.components.findIndex(c => c.id === id)
    if (idx === -1) return
    const comps = [...templateConfig.value.components]
    comps[idx] = { ...comps[idx], ...updates }
    templateConfig.value = {
      ...templateConfig.value,
      components: comps,
    }
  }

  /** 更新组件样式 */
  function updateComponentStyles(id: string, styles: Partial<ComponentStyles>) {
    const idx = templateConfig.value.components.findIndex(c => c.id === id)
    if (idx === -1) return
    const comps = [...templateConfig.value.components]
    comps[idx] = {
      ...comps[idx],
      styles: { ...(comps[idx].styles || {}), ...styles },
    }
    templateConfig.value = {
      ...templateConfig.value,
      components: comps,
    }
  }

  /** 更新组件特有属性 */
  function updateComponentProps(id: string, propUpdates: Record<string, any>) {
    const idx = templateConfig.value.components.findIndex(c => c.id === id)
    if (idx === -1) return
    const comps = [...templateConfig.value.components]
    comps[idx] = {
      ...comps[idx],
      props: { ...(comps[idx].props || {}), ...propUpdates },
    }
    templateConfig.value = {
      ...templateConfig.value,
      components: comps,
    }
  }

  /** 更新组件数据源 */
  function updateDataSource(id: string, ds: Partial<DataSourceConfig> | undefined) {
    const idx = templateConfig.value.components.findIndex(c => c.id === id)
    if (idx === -1) return
    const comps = [...templateConfig.value.components]
    const existing = comps[idx].dataSource
    if (ds === undefined) {
      comps[idx] = { ...comps[idx], dataSource: undefined }
    } else {
      comps[idx] = {
        ...comps[idx],
        dataSource: { ...(existing || {}), ...ds } as DataSourceConfig,
      }
    }
    templateConfig.value = {
      ...templateConfig.value,
      components: comps,
    }
  }

  /** 更新组件动画 */
  function updateComponentAnimation(id: string, anim: Partial<AnimationConfig> | undefined) {
    const idx = templateConfig.value.components.findIndex(c => c.id === id)
    if (idx === -1) return
    const comps = [...templateConfig.value.components]
    if (anim === undefined) {
      comps[idx] = { ...comps[idx], animation: undefined }
    } else {
      const existing = comps[idx].animation || { type: 'none' }
      comps[idx] = {
        ...comps[idx],
        animation: { ...existing, ...anim } as AnimationConfig,
      }
    }
    templateConfig.value = {
      ...templateConfig.value,
      components: comps,
    }
  }

  /** 更新画布配置 */
  function updateCanvas(updates: Partial<CanvasConfig>) {
    templateConfig.value = {
      ...templateConfig.value,
      canvas: {
        ...templateConfig.value.canvas,
        ...updates,
      },
    }
  }

  /** 更新画布背景配置 */
  function updateCanvasBackground(bgUpdates: Record<string, any>) {
    const existing = templateConfig.value.canvas.background || { type: 'color' }
    templateConfig.value = {
      ...templateConfig.value,
      canvas: {
        ...templateConfig.value.canvas,
        background: { ...existing, ...bgUpdates } as any,
      },
    }
  }

  /** 更新画布主题 */
  function updateCanvasTheme(themeUpdates: Record<string, any>) {
    const existing = templateConfig.value.canvas.theme || {}
    templateConfig.value = {
      ...templateConfig.value,
      canvas: {
        ...templateConfig.value.canvas,
        theme: { ...existing, ...themeUpdates } as any,
      },
    }
  }

  /** 添加组件到指定位置 */
  function addComponent(type: ComponentType, x: number, y: number, name?: string): ComponentConfig {
    pushHistory()

    const defaults = getComponentDefault(type, name)
    const newComp: ComponentConfig = {
      id: generateId(),
      x,
      y,
      ...defaults,
    }

    templateConfig.value = {
      ...templateConfig.value,
      components: [...templateConfig.value.components, newComp],
    }

    return newComp
  }

  /** 删除组件 */
  function removeComponent(id: string) {
    pushHistory()

    templateConfig.value = {
      ...templateConfig.value,
      components: templateConfig.value.components.filter(c => c.id !== id),
    }

    if (selectedComponentId.value === id) {
      selectedComponentId.value = null
    }
  }

  /** 更新组件位置（不记录历史，用于拖拽实时更新） */
  function updateComponentPosition(id: string, x: number, y: number): void {
    const idx = templateConfig.value.components.findIndex(c => c.id === id)
    if (idx === -1) return

    const comps = [...templateConfig.value.components]
    comps[idx] = { ...comps[idx], x, y }
    templateConfig.value = {
      ...templateConfig.value,
      components: comps,
    }
  }

  /** 确认组件位置（拖拽结束时调用，记录历史） */
  function confirmComponentPosition(id: string, x: number, y: number): void {
    pushHistory()
    updateComponentPosition(id, x, y)
  }

  /** 更新组件尺寸（不记录历史，用于缩放手柄实时调整） */
  function updateComponentSize(id: string, width: number, height: number, x?: number, y?: number): void {
    const idx = templateConfig.value.components.findIndex(c => c.id === id)
    if (idx === -1) return
    const comps = [...templateConfig.value.components]
    const update: Partial<ComponentConfig> = { width, height }
    if (x !== undefined) update.x = x
    if (y !== undefined) update.y = y
    comps[idx] = { ...comps[idx], ...update }
    templateConfig.value = {
      ...templateConfig.value,
      components: comps,
    }
  }

  /** 确认组件尺寸（缩放手柄松手时调用，记录历史） */
  function confirmComponentSize(id: string, width: number, height: number, x?: number, y?: number): void {
    pushHistory()
    updateComponentSize(id, width, height, x, y)
  }

  /** 复制组件 */
  function duplicateComponent(id: string): ComponentConfig | null {
    const source = templateConfig.value.components.find(c => c.id === id)
    if (!source) return null

    pushHistory()

    const newComp: ComponentConfig = {
      ...source,
      id: generateId(),
      x: source.x + 20,
      y: source.y + 20,
    }

    templateConfig.value = {
      ...templateConfig.value,
      components: [...templateConfig.value.components, newComp],
    }

    // 自动选中新复制的组件
    selectedComponentId.value = newComp.id

    return newComp
  }

  /** 更新组件 zIndex（带历史记录） */
  function bringToFront(id: string) {
    pushHistory()
    const idx = templateConfig.value.components.findIndex(c => c.id === id)
    if (idx === -1) return

    const comps = [...templateConfig.value.components]
    const comp = comps[idx]
    const maxZ = Math.max(...comps.map(c => c.zIndex), 0)
    comps[idx] = { ...comp, zIndex: maxZ + 1 }

    templateConfig.value = {
      ...templateConfig.value,
      components: comps,
    }
  }

  /** 上移一层 */
  function moveLayerUp(id: string) {
    pushHistory()
    const idx = templateConfig.value.components.findIndex(c => c.id === id)
    if (idx === -1) return

    const comps = [...templateConfig.value.components]
    const comp = comps[idx]
    // 找到 zIndex 大于当前且最小的
    const sortedAsc = [...comps].sort((a, b) => a.zIndex - b.zIndex)
    const currentPos = sortedAsc.findIndex(c => c.id === id)
    if (currentPos < sortedAsc.length - 1) {
      const above = sortedAsc[currentPos + 1]
      // 交换 zIndex
      const tempZ = comp.zIndex
      const aboveIdx = comps.findIndex(c => c.id === above.id)
      comps[idx] = { ...comp, zIndex: above.zIndex }
      comps[aboveIdx] = { ...above, zIndex: tempZ }
    } else {
      // 已经在最顶层，直接置顶
      const maxZ = Math.max(...comps.map(c => c.zIndex), 0)
      comps[idx] = { ...comp, zIndex: maxZ + 1 }
    }

    templateConfig.value = {
      ...templateConfig.value,
      components: comps,
    }
  }

  /** 下移一层 */
  function moveLayerDown(id: string) {
    pushHistory()
    const idx = templateConfig.value.components.findIndex(c => c.id === id)
    if (idx === -1) return

    const comps = [...templateConfig.value.components]
    const comp = comps[idx]
    // 找到 zIndex 小于当前且最大的
    const sortedAsc = [...comps].sort((a, b) => a.zIndex - b.zIndex)
    const currentPos = sortedAsc.findIndex(c => c.id === id)
    if (currentPos > 0) {
      const below = sortedAsc[currentPos - 1]
      const tempZ = comp.zIndex
      const belowIdx = comps.findIndex(c => c.id === below.id)
      comps[idx] = { ...comp, zIndex: below.zIndex }
      comps[belowIdx] = { ...below, zIndex: tempZ }
    }
    // 已经在最底层，不做操作

    templateConfig.value = {
      ...templateConfig.value,
      components: comps,
    }
  }

  /** 置底 */
  function moveLayerToBottom(id: string) {
    pushHistory()
    const idx = templateConfig.value.components.findIndex(c => c.id === id)
    if (idx === -1) return

    const comps = [...templateConfig.value.components]
    const comp = comps[idx]
    const minZ = Math.min(...comps.map(c => c.zIndex), 0)
    comps[idx] = { ...comp, zIndex: minZ - 1 }

    templateConfig.value = {
      ...templateConfig.value,
      components: comps,
    }
  }

  /** 切换组件可见性 */
  function toggleComponentVisibility(id: string) {
    pushHistory()
    const idx = templateConfig.value.components.findIndex(c => c.id === id)
    if (idx === -1) return

    const comps = [...templateConfig.value.components]
    comps[idx] = { ...comps[idx], visible: !comps[idx].visible }

    templateConfig.value = {
      ...templateConfig.value,
      components: comps,
    }
  }

  /** 切换组件锁定 */
  function toggleComponentLock(id: string) {
    pushHistory()
    const idx = templateConfig.value.components.findIndex(c => c.id === id)
    if (idx === -1) return

    const comps = [...templateConfig.value.components]
    comps[idx] = { ...comps[idx], locked: !comps[idx].locked }

    templateConfig.value = {
      ...templateConfig.value,
      components: comps,
    }
  }

  return {
    // 状态
    templateConfig,
    selectedComponentId,
    selectedComponent,
    zoom,
    history,
    historyIndex,
    canUndo,
    canRedo,
    componentCount,
    gridConfig,
    templateEditMode,
    // 操作
    pushHistory,
    undo,
    redo,
    selectComponent,
    setZoom,
    snapToGrid,
    addComponent,
    removeComponent,
    updateComponentPosition,
    confirmComponentPosition,
    duplicateComponent,
    bringToFront,
    moveLayerUp,
    moveLayerDown,
    moveLayerToBottom,
    toggleComponentVisibility,
    toggleComponentLock,
    generateId,
    toggleTemplateEditMode,
    updateComponent,
    updateComponentSize,
    confirmComponentSize,
    updateComponentStyles,
    updateComponentProps,
    updateDataSource,
    updateComponentAnimation,
    updateCanvas,
    updateCanvasBackground,
    updateCanvasTheme,
  }
}
