<script setup lang="ts">
/**
 * 大屏设计器 - 根组件
 *
 * 整体布局：
 * ┌─────────────────────────────────────────────────────────┐
 * │  ToolbarPanel（顶部工具栏）                               │
 * ├───────────┬─────────────────────────────────┬────────────┤
 * │  组件面板   │        Canvas 画布               │  属性面板   │
 * │  Component│        CanvasWorkspace         │  Property  │
 * │  Panel    │    （拖拽/缩放/选中/辅助线）      │  Panel     │
 * ├───────────┴─────────────────────────────────┴────────────┤
 * │  底部状态栏 StatusBar                                       │
 * └─────────────────────────────────────────────────────────┘
 *
 * 支持从 URL 参数加载已有模板（通过 dataset 传递）
 * 保存时调用 API 新建或更新模板
 */
import { onMounted, onUnmounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useDesignerState } from './composables/useDesignerState'
import { createTemplate, updateTemplate } from '@/services/largeScreenApi'
import { parseTemplateConfig } from '@/types/template-editor'
import type {
  ComponentType,
  ComponentConfig,
  TemplateConfig,
  ComponentStyles,
  DataSourceConfig,
  AnimationConfig,
  CanvasConfig,
} from '@/types/template-editor'
import ToolbarPanel from './ToolbarPanel.vue'
import ComponentPanel from './ComponentPanel.vue'
import CanvasWorkspace from './CanvasWorkspace.vue'
import PropertyPanel from './PropertyPanel.vue'
import StatusBar from './StatusBar.vue'

const designer = useDesignerState()

// ─── 模板元数据 ─────────────────────────────────────

/** 当前是否在编辑已有模板 */
const editingTemplateId = ref<string | null>(null)
const templateName = ref('')
const saving = ref(false)

// ─── 初始加载：从 URL 参数载入模板 ─────────────────

onMounted(() => {
  const appEl = document.getElementById('app')
  if (appEl) {
    const tid = appEl.dataset.templateId
    const name = appEl.dataset.templateName
    const configStr = appEl.dataset.templateConfig

    if (tid && configStr) {
      try {
        const config = JSON.parse(configStr) as TemplateConfig
        designer.templateConfig.value = config
        editingTemplateId.value = tid
        templateName.value = name || ''
      } catch {
        // 解析失败，使用空模板
      }
    }
  }

  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})

// ─── 面板折叠 ─────────────────────────────────────

const leftCollapsed = ref(false)
const rightCollapsed = ref(false)

// ─── 键盘事件 ─────────────────────────────────────

function handleKeyDown(event: KeyboardEvent) {
  const selectedId = designer.selectedComponentId.value
  if (!selectedId) return

  // 如果焦点在输入框内，不处理键盘快捷键
  const tag = (event.target as HTMLElement)?.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return

  // Delete / Backspace → 删除组件
  if (event.key === 'Delete' || event.key === 'Backspace') {
    // Backspace 在 Mac 上相当于删除
    event.preventDefault()
    designer.removeComponent(selectedId)
    return
  }

  // Ctrl+C / Ctrl+V → 复制粘贴
  if (event.ctrlKey || event.metaKey) {
    if (event.key === 'c') {
      event.preventDefault()
      designer.duplicateComponent(selectedId)
      return
    }
    // Ctrl+D → 复制（类似 Sketch/Figam）
    if (event.key === 'd') {
      event.preventDefault()
      designer.duplicateComponent(selectedId)
      return
    }
  }
}

// ─── 保存模板 ─────────────────────────────────────

async function handleSave() {
  saving.value = true
  try {
    const name = templateName.value.trim() || '未命名模板'
    const config = designer.templateConfig.value

    if (editingTemplateId.value) {
      // 编辑已有模板 → PUT
      await updateTemplate(editingTemplateId.value, {
        name,
        templateConfig: config,
        canvasWidth: config.canvas.width,
        canvasHeight: config.canvas.height,
        backgroundColor: config.canvas.backgroundColor,
      })
      message.success('模板已保存')
    } else {
      // 新建模板 → POST
      const result = await createTemplate({
        name,
        templateConfig: config,
        canvasWidth: config.canvas.width,
        canvasHeight: config.canvas.height,
        backgroundColor: config.canvas.backgroundColor,
      })
      editingTemplateId.value = result.id
      message.success('模板已创建')
    }
  } catch (e: any) {
    message.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

// ─── 预览 ─────────────────────────────────────

async function handlePreview() {
  // 先保存模板获取模板ID，再打开预览
  await handleSave()
  const tid = editingTemplateId.value || designer.getTemplateId?.()
  if (tid) {
    window.open(`/large-screen.html?templateId=${tid}`, '_blank')
  }
}

// ─── 导入/导出 ─────────────────────────────────────

function handleImport() {
  console.log('import template')
}

function handleExport() {
  console.log('export template')
}

function handleTemplateNameUpdate(name: string) {
  templateName.value = name
}

// ─── 画布操作 ─────────────────────────────────────

function handleSelectComponent(id: string | null) {
  designer.selectComponent(id)
}

function handleAddComponent(type: ComponentType, x: number, y: number) {
  designer.addComponent(type, x, y)
}

function handleRemoveComponent(id: string) {
  designer.removeComponent(id)
}

function handleDuplicateComponent(id: string) {
  designer.duplicateComponent(id)
}

function handleBringToFront(id: string) {
  designer.bringToFront(id)
}

function handleUpdateComponentPosition(id: string, x: number, y: number) {
  designer.updateComponentPosition(id, x, y)
}

function handleConfirmComponentPosition(id: string, x: number, y: number) {
  designer.confirmComponentPosition(id, x, y)
}

function handleUpdateComponentSize(id: string, width: number, height: number, x?: number, y?: number) {
  designer.updateComponentSize(id, width, height, x, y)
}

function handleConfirmComponentSize(id: string, width: number, height: number, x?: number, y?: number) {
  designer.confirmComponentSize(id, width, height, x, y)
}

// ─── 点击添加组件（从组件面板点击） ──────────────

function handleAddComponentByClick(type: ComponentType) {
  // 点击添加：放到画布中心
  const cw = designer.templateConfig.value.canvas.width
  const ch = designer.templateConfig.value.canvas.height
  const centerX = Math.round(cw / 2)
  const centerY = Math.round(ch / 2)
  designer.addComponent(type, centerX, centerY)
}
</script>

<template>
  <div class="large-screen-designer h-screen flex flex-col bg-[#0a192f] overflow-hidden">
    <!-- 顶部工具栏 -->
    <ToolbarPanel
      :template-name="templateName"
      :can-undo="designer.canUndo.value"
      :can-redo="designer.canRedo.value"
      :zoom="designer.zoom.value"
      :saving="saving"
      @save="handleSave"
      @preview="handlePreview"
      @undo="designer.undo()"
      @redo="designer.redo()"
      @update:zoom="designer.setZoom($event)"
      @import="handleImport"
      @export="handleExport"
      @update:template-name="handleTemplateNameUpdate"
    />

    <!-- 主体区域 -->
    <div class="flex-1 flex overflow-hidden">
      <!-- 左侧组件面板（含图层面板） -->
      <div class="relative flex-shrink-0" :style="{ width: leftCollapsed ? '0px' : '260px', transition: 'width 0.2s ease' }">
        <div class="w-[260px] h-full overflow-hidden">
          <ComponentPanel
            :components="designer.templateConfig.value.components"
            :selected-component-id="designer.selectedComponentId.value"
            @add-component-by-click="handleAddComponentByClick"
            @select-component="designer.selectComponent"
            @bring-to-front="designer.bringToFront"
            @move-layer-up="designer.moveLayerUp"
            @move-layer-down="designer.moveLayerDown"
            @move-layer-to-bottom="designer.moveLayerToBottom"
            @toggle-component-visibility="designer.toggleComponentVisibility"
            @toggle-component-lock="designer.toggleComponentLock"
          />
        </div>
      </div>
      <!-- 左侧折叠按钮（在外层，不被overflow影响） -->
      <button
        class="z-30 w-6 h-10 mt-[50vh] flex-shrink-0 rounded-r-md bg-[#112240] border border-[#1e293b] border-l-0 flex items-center justify-center cursor-pointer hover:bg-[#172a45] transition-colors"
        @click="leftCollapsed = !leftCollapsed"
        :title="leftCollapsed ? '展开组件面板' : '折叠组件面板'"
      >
        <svg class="w-3.5 h-3.5 text-[#8892a0] transition-transform duration-200" :class="{ 'rotate-180': leftCollapsed }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="15 18 9 12 15 6" />
        </svg>
      </button>

      <!-- 中间画布 -->
      <CanvasWorkspace
        :template-config="designer.templateConfig.value"
        :zoom="designer.zoom.value"
        class="flex-1"
        @select-component="handleSelectComponent"
        @add-component="handleAddComponent"
        @remove-component="handleRemoveComponent"
        @duplicate-component="handleDuplicateComponent"
        @bring-to-front="handleBringToFront"
        @update-component-position="handleUpdateComponentPosition"
        @confirm-component-position="handleConfirmComponentPosition"
        @update-component-size="handleUpdateComponentSize"
        @confirm-component-size="handleConfirmComponentSize"
      />

      <!-- 右侧折叠按钮（在外层，不被overflow影响） -->
      <button
        class="z-30 w-6 h-10 mt-[50vh] flex-shrink-0 rounded-l-md bg-[#112240] border border-[#1e293b] border-r-0 flex items-center justify-center cursor-pointer hover:bg-[#172a45] transition-colors"
        @click="rightCollapsed = !rightCollapsed"
        :title="rightCollapsed ? '展开属性面板' : '折叠属性面板'"
      >
        <svg class="w-3.5 h-3.5 text-[#8892a0] transition-transform duration-200" :class="{ 'rotate-180': rightCollapsed }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="9 18 15 12 9 6" />
        </svg>
      </button>

      <!-- 右侧属性面板 -->
      <div class="relative flex-shrink-0" :style="{ width: rightCollapsed ? '0px' : '300px', transition: 'width 0.2s ease' }">
        <div class="w-[300px] h-full overflow-hidden">
          <PropertyPanel
            :selected-component="designer.selectedComponent.value"
            :template-config="designer.templateConfig.value"
            :template-edit-mode="designer.templateEditMode.value"
            :selected-component-id="designer.selectedComponentId.value"
            @toggle-template-edit-mode="designer.toggleTemplateEditMode()"
            @update-component="designer.updateComponent"
            @update-component-styles="designer.updateComponentStyles"
            @update-component-props="designer.updateComponentProps"
            @update-data-source="designer.updateDataSource"
            @update-component-animation="designer.updateComponentAnimation"
            @update-canvas="designer.updateCanvas"
            @update-canvas-background="designer.updateCanvasBackground"
            @update-canvas-theme="designer.updateCanvasTheme"
            @push-history="designer.pushHistory"
            @select-component="designer.selectComponent"
          />
        </div>
      </div>
    </div>

    <!-- 底部状态栏 -->
    <StatusBar
      :canvas-width="designer.templateConfig.value.canvas.width"
      :canvas-height="designer.templateConfig.value.canvas.height"
      :zoom="designer.zoom.value"
      :component-count="designer.componentCount.value"
      :selected-component="designer.selectedComponent.value"
    />
  </div>
</template>

<style scoped>
.large-screen-designer {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  color: #ccd6f6;
}
</style>
