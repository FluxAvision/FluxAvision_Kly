/**
 * 模板编辑器状态管理
 */
import { ref, computed, reactive, watch } from 'vue'
import { v4 as uuidv4 } from 'uuid'
import { message } from 'ant-design-vue'
import type { TemplateConfig, ComponentConfig, CanvasConfig } from '@/types/template-editor'
import { createEmptyTemplate, getComponentDefault, parseTemplateConfig } from '@/types/template-editor'

export function useTemplateEditor(initialConfig?: TemplateConfig | string | null) {
  // 模板配置
  const template = ref<TemplateConfig>(parseTemplateConfig(initialConfig))

  // 当前选中的组件
  const selectedComponent = ref<ComponentConfig | null>(null)

  // 历史记录
  const history = reactive<string[]>([])
  const historyIndex = ref(-1)

  // 保存状态
  const saving = ref(false)
  const hasChanges = ref(false)

  // 计算属性
  const components = computed(() => template.value.components)
  const canvasConfig = computed(() => template.value.canvas)

  // 添加组件
  function addComponent(type: string, position: { x: number; y: number }) {
    const defaultConfig = getComponentDefault(type as any)
    const newComponent: ComponentConfig = {
      ...defaultConfig,
      id: `comp-${uuidv4().slice(0, 8)}`,
      x: position.x,
      y: position.y,
      zIndex: template.value.components.length + 1,
    }

    template.value.components.push(newComponent)
    saveHistory()
    selectComponent(newComponent)
    hasChanges.value = true

    return newComponent
  }

  // 更新组件
  function updateComponent(id: string, updates: Partial<ComponentConfig>) {
    const index = template.value.components.findIndex(c => c.id === id)
    if (index > -1) {
      template.value.components[index] = {
        ...template.value.components[index],
        ...updates,
      }
      // 同步更新选中组件
      if (selectedComponent.value?.id === id) {
        selectedComponent.value = template.value.components[index]
      }
      hasChanges.value = true
    }
  }

  // 删除组件
  function deleteComponent(id: string) {
    const index = template.value.components.findIndex(c => c.id === id)
    if (index > -1) {
      template.value.components.splice(index, 1)
      if (selectedComponent.value?.id === id) {
        selectedComponent.value = null
      }
      saveHistory()
      hasChanges.value = true
    }
  }

  // 选择组件
  function selectComponent(component: ComponentConfig | null) {
    selectedComponent.value = component
  }

  // 移动组件
  function moveComponent(id: string, position: { x: number; y: number }) {
    const { grid } = template.value.canvas
    let { x, y } = position

    // 网格吸附
    if (grid.snapToGrid && grid.enabled) {
      x = Math.round(x / grid.size) * grid.size
      y = Math.round(y / grid.size) * grid.size
    }

    updateComponent(id, { x, y })
  }

  // 调整组件大小
  function resizeComponent(id: string, size: { width: number; height: number }, position?: { x: number; y: number }) {
    const updates: Partial<ComponentConfig> = { ...size }
    if (position) {
      updates.x = position.x
      updates.y = position.y
    }
    updateComponent(id, updates)
  }

  // 更新画布配置
  function updateCanvas(updates: Partial<CanvasConfig>) {
    template.value.canvas = { ...template.value.canvas, ...updates }
    hasChanges.value = true
  }

  // 历史管理
  function saveHistory() {
    const state = JSON.stringify(template.value)
    // 删除当前位置之后的历史
    history.splice(historyIndex.value + 1)
    history.push(state)
    historyIndex.value = history.length - 1

    // 限制历史记录数量
    if (history.length > 50) {
      history.shift()
      historyIndex.value--
    }
  }

  function undo() {
    if (historyIndex.value > 0) {
      historyIndex.value--
      template.value = JSON.parse(history[historyIndex.value])
      selectedComponent.value = null
    }
  }

  function redo() {
    if (historyIndex.value < history.length - 1) {
      historyIndex.value++
      template.value = JSON.parse(history[historyIndex.value])
      selectedComponent.value = null
    }
  }

  const canUndo = computed(() => historyIndex.value > 0)
  const canRedo = computed(() => historyIndex.value < history.length - 1)

  // 重置模板
  function resetTemplate() {
    template.value = createEmptyTemplate()
    selectedComponent.value = null
    history.splice(0)
    historyIndex.value = -1
    hasChanges.value = false
  }

  // 加载模板配置
  function loadTemplate(config: TemplateConfig | string) {
    template.value = parseTemplateConfig(config)
    selectedComponent.value = null
    saveHistory()
    hasChanges.value = false
  }

  // 导出配置
  function exportConfig(): TemplateConfig {
    return JSON.parse(JSON.stringify(template.value))
  }

  // 保存到后端
  async function saveTemplate(templateId?: string, meta?: { name?: string; description?: string }) {
    saving.value = true
    try {
      const config = exportConfig()
      const body = {
        ...meta,
        templateConfig: config,
        canvasWidth: config.canvas.width,
        canvasHeight: config.canvas.height,
        backgroundColor: config.canvas.backgroundColor,
        backgroundImage: config.canvas.backgroundImage,
      }

      let res: Response
      if (templateId) {
        res = await fetch(`/api/large-screen/templates/${templateId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        })
      } else {
        res = await fetch('/api/large-screen/templates', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        })
      }

      if (res.ok) {
        const json = await res.json()
        hasChanges.value = false
        message.success('模板保存成功')
        return json.data
      } else {
        const errData = await res.json().catch(() => ({}))
        message.error(`保存失败: ${errData.message || res.statusText}`)
        return null
      }
    } catch (e: any) {
      message.error(`保存失败: ${e.message || '网络错误'}`)
      return null
    } finally {
      saving.value = false
    }
  }

  // 初始化历史
  watch(() => template.value, () => {
    if (history.length === 0) {
      saveHistory()
    }
  }, { immediate: true, deep: true })

  // 标记有更改（用于名称修改等非模板内容变更）
  function markHasChanges() {
    hasChanges.value = true
  }

  return {
    template,
    selectedComponent,
    components,
    canvasConfig,
    saving,
    hasChanges,
    // 操作方法
    addComponent,
    updateComponent,
    deleteComponent,
    selectComponent,
    moveComponent,
    resizeComponent,
    updateCanvas,
    // 历史
    undo,
    redo,
    canUndo,
    canRedo,
    saveHistory,
    // 其他
    resetTemplate,
    loadTemplate,
    exportConfig,
    saveTemplate,
    markHasChanges,
  }
}
