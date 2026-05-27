<script setup lang="ts">
/**
 * 顶部工具栏 - ToolbarPanel.vue
 *
 * 功能：
 * - 保存 / 预览
 * - 撤销 / 重做
 * - 导入 / 导出
 * - 缩放控制（缩小/放大/比例显示/下拉选择预设）
 */
import { computed } from 'vue'

const props = defineProps<{
  templateName: string
  canUndo: boolean
  canRedo: boolean
  zoom: number
  saving: boolean
}>()

const emit = defineEmits<{
  save: []
  preview: []
  undo: []
  redo: []
  'update:zoom': [value: number]
  import: []
  export: []
  'update:template-name': [name: string]
}>()

// ─── 缩放预设 ───────────────────────────────────

const zoomPresets = computed(() => {
  return [25, 50, 75, 100, 125, 150, 200]
})

function handleZoomOut() {
  const newZoom = Math.max(25, props.zoom - 10)
  emit('update:zoom', newZoom)
}

function handleZoomIn() {
  const newZoom = Math.min(500, props.zoom + 10)
  emit('update:zoom', newZoom)
}

function handleZoomSelect(event: Event) {
  const val = parseInt((event.target as HTMLSelectElement).value)
  if (!isNaN(val)) {
    emit('update:zoom', val)
  }
}

function handleTemplateNameInput(event: Event) {
  const val = (event.target as HTMLInputElement).value
  emit('update:template-name', val)
}
</script>

<template>
  <div
    class="toolbar h-12 flex items-center justify-between px-3 bg-[#112240] border-b border-[#1e293b] select-none"
  >
    <!-- 左侧：模板名称 -->
    <div class="flex items-center gap-3">
      <input
        :value="templateName"
        @input="handleTemplateNameInput"
        type="text"
        class="bg-transparent border border-transparent hover:border-[#1e293b] focus:border-[#00d9ff] rounded-md px-2.5 py-1 text-sm font-medium text-white outline-none transition-colors w-40"
        placeholder="未命名模板"
      />
    </div>

    <!-- 中间：操作按钮组 -->
    <div class="flex items-center gap-1">
      <!-- 保存 -->
      <button
        :disabled="saving"
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#00d9ff] text-[#0a192f] text-xs font-semibold hover:bg-[#00d9ff]/80 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-colors"
        @click="emit('save')"
      >
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z" />
          <polyline points="17 21 17 13 7 13 7 21" />
          <polyline points="7 3 7 8 15 8" />
        </svg>
        {{ saving ? '保存中...' : '保存' }}
      </button>

      <!-- 预览 -->
      <button
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#0a192f] border border-[#1e293b] text-[#ccd6f6] text-xs hover:bg-[#172a45] hover:border-[#00d9ff]/30 cursor-pointer transition-colors"
        @click="emit('preview')"
      >
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
          <circle cx="12" cy="12" r="3" />
        </svg>
        预览
      </button>

      <div class="w-px h-6 bg-[#1e293b] mx-1" />

      <!-- 撤销 -->
      <button
        :disabled="!canUndo"
        class="flex items-center justify-center w-8 h-8 rounded-md bg-[#0a192f] border border-[#1e293b] text-[#8892a0] hover:text-white hover:border-[#00d9ff]/30 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer transition-colors"
        title="撤销 (Ctrl+Z)"
        @click="emit('undo')"
      >
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="1 4 1 10 7 10" />
          <path d="M3.51 15a9 9 0 102.13-9.36L1 10" />
        </svg>
      </button>

      <!-- 重做 -->
      <button
        :disabled="!canRedo"
        class="flex items-center justify-center w-8 h-8 rounded-md bg-[#0a192f] border border-[#1e293b] text-[#8892a0] hover:text-white hover:border-[#00d9ff]/30 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer transition-colors"
        title="重做 (Ctrl+Shift+Z)"
        @click="emit('redo')"
      >
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="23 4 23 10 17 10" />
          <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10" />
        </svg>
      </button>

      <div class="w-px h-6 bg-[#1e293b] mx-1" />

      <!-- 导入 -->
      <button
        class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-[#0a192f] border border-[#1e293b] text-[#8892a0] text-xs hover:text-white hover:border-[#00d9ff]/30 cursor-pointer transition-colors"
        title="导入模板"
        @click="emit('import')"
      >
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
          <polyline points="7 10 12 15 17 10" />
          <line x1="12" y1="15" x2="12" y2="3" />
        </svg>
        导入
      </button>

      <!-- 导出 -->
      <button
        class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-[#0a192f] border border-[#1e293b] text-[#8892a0] text-xs hover:text-white hover:border-[#00d9ff]/30 cursor-pointer transition-colors"
        title="导出模板"
        @click="emit('export')"
      >
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
        导出
      </button>
    </div>

    <!-- 右侧：缩放控制 -->
    <div class="flex items-center gap-1.5">
      <!-- 缩小 -->
      <button
        class="flex items-center justify-center w-7 h-7 rounded-md bg-[#0a192f] border border-[#1e293b] text-[#8892a0] hover:text-white hover:border-[#00d9ff]/30 cursor-pointer transition-colors"
        title="缩小"
        @click="handleZoomOut"
      >
        <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
          <line x1="8" y1="11" x2="14" y2="11" />
        </svg>
      </button>

      <!-- 缩放下拉 -->
      <select
        :value="zoom"
        @change="handleZoomSelect"
        class="w-16 h-7 rounded-md bg-[#0a192f] border border-[#1e293b] text-xs text-white text-center outline-none cursor-pointer appearance-none px-1 hover:border-[#00d9ff]/30 transition-colors"
      >
        <option
          v-for="p in zoomPresets"
          :key="p"
          :value="p"
        >
          {{ p }}%
        </option>
      </select>

      <!-- 放大 -->
      <button
        class="flex items-center justify-center w-7 h-7 rounded-md bg-[#0a192f] border border-[#1e293b] text-[#8892a0] hover:text-white hover:border-[#00d9ff]/30 cursor-pointer transition-colors"
        title="放大"
        @click="handleZoomIn"
      >
        <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
          <line x1="11" y1="8" x2="11" y2="14" />
          <line x1="8" y1="11" x2="14" y2="11" />
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.toolbar {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.toolbar select {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='8' height='8' viewBox='0 0 24 24' fill='none' stroke='%238892a0' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 4px center;
  padding-right: 16px;
}
</style>
