<script setup lang="ts">
/**
 * 模板编辑器主入口
 */
import { ref, computed, onMounted, provide, watch } from 'vue'
import { useTemplateEditor } from './composables/useTemplateEditor'
import type { ComponentConfig, TemplateConfig } from '@/types/template-editor'
import ComponentPanel from './panels/ComponentPanel.vue'
import CanvasPanel from './panels/CanvasPanel.vue'
import PropertyPanel from './panels/PropertyPanel.vue'
import ToolbarPanel from './panels/ToolbarPanel.vue'
import TemplateRenderer from '@/components/large-screen/TemplateRenderer.vue'

const props = defineProps<{
  templateId?: string
  templateName?: string
  initialConfig?: TemplateConfig | string
}>()

const emit = defineEmits<{
  saved: [template: any]
  renamed: [name: string]
  back: []
}>()

const {
  template,
  selectedComponent,
  components,
  canvasConfig,
  saving,
  hasChanges,
  addComponent,
  updateComponent,
  deleteComponent,
  selectComponent,
  moveComponent,
  resizeComponent,
  updateCanvas,
  undo,
  redo,
  canUndo,
  canRedo,
  saveTemplate,
  exportConfig,
  markHasChanges,
} = useTemplateEditor(props.initialConfig)

// 模板名称
const templateName = ref(props.templateName || '')

// 预览模式
const previewMode = ref(false)

// 监听 props 变化
watch(() => props.templateName, (newName) => {
  if (newName) {
    templateName.value = newName
  }
}, { immediate: true })

// 添加组件（默认位置在画布中心）
function handleAddComponent(type: string) {
  const x = (canvasConfig.value.width / 2) - 100
  const y = (canvasConfig.value.height / 2) - 50
  addComponent(type, { x, y })
}

// 处理保存
async function handleSave() {
  const result = await saveTemplate(props.templateId, { name: templateName.value || undefined })
  if (result) {
    emit('saved', result)
  }
}

// 处理重命名
function handleRename(name: string) {
  templateName.value = name
  // 标记有更改，这样用户可以保存
  markHasChanges()
}

// 处理预览
function handlePreview() {
  previewMode.value = !previewMode.value
}

// 处理画布配置更新（背景等）
function handleUpdateCanvas(updates: { backgroundColor?: string; backgroundImage?: string }) {
  updateCanvas(updates)
  markHasChanges()
}

// 提供给子组件
provide('templateEditor', {
  template,
  selectedComponent,
  components,
  canvasConfig,
})
</script>

<template>
  <div class="template-editor h-screen flex flex-col bg-[#0a192f] overflow-hidden">
    <!-- 预览模式 -->
    <div v-if="previewMode" class="relative h-full">
      <div class="absolute top-4 right-4 z-50 flex gap-2">
        <button
          class="px-4 py-2 rounded bg-white/10 hover:bg-white/20 text-white transition-colors cursor-pointer"
          @click="previewMode = false"
        >
          关闭预览
        </button>
      </div>
      <TemplateRenderer :config="template" />
    </div>

    <!-- 编辑模式 -->
    <template v-else>
      <!-- 顶部工具栏 -->
      <ToolbarPanel
        :can-undo="canUndo"
        :can-redo="canRedo"
        :saving="saving"
        :has-changes="hasChanges"
        :template-name="templateName"
        :canvas-config="canvasConfig"
        @save="handleSave"
        @preview="handlePreview"
        @undo="undo"
        @redo="redo"
        @back="emit('back')"
        @rename="handleRename"
        @update-canvas="handleUpdateCanvas"
      />

      <!-- 主体区域 -->
      <div class="flex-1 flex overflow-hidden">
        <!-- 左侧组件面板 -->
        <ComponentPanel
          class="w-56 flex-shrink-0"
          @add-component="handleAddComponent"
        />

        <!-- 中间画布 -->
        <CanvasPanel
          class="flex-1"
          :components="components"
          :canvas-config="canvasConfig"
          :selected-id="selectedComponent?.id || null"
          @select="selectComponent"
          @move="moveComponent"
          @resize="resizeComponent"
        />

        <!-- 右侧属性面板 -->
        <PropertyPanel
          class="w-72 flex-shrink-0"
          :component="selectedComponent"
          @update="updateComponent"
          @delete="deleteComponent"
        />
      </div>
    </template>
  </div>
</template>
