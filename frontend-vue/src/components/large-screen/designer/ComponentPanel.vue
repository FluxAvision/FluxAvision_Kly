<script setup lang="ts">
/**
 * 左侧组件面板 - 上半部组件列表 + 下半部图层面板（50/50分屏）
 *
 * 上半部：
 * - 按分类列出 COMPONENT_DEFINITIONS 中定义的组件
 * - 点击添加到画布中心
 * - 拖拽到画布（通过 HTML5 Drag API）
 *
 * 下半部：
 * - 显示/插槽集成 LayerPanel
 */
import { ref, computed } from 'vue'
import type { ComponentConfig, ComponentType } from '@/types/template-editor'
import { COMPONENT_DEFINITIONS } from '@/types/template-editor'

const props = defineProps<{
  components: ComponentConfig[]
  selectedComponentId: string | null
}>()

const emit = defineEmits<{
  'add-component-by-click': [type: ComponentType]
  'select-component': [id: string | null]
  'bring-to-front': [id: string]
  'move-layer-up': [id: string]
  'move-layer-down': [id: string]
  'move-layer-to-bottom': [id: string]
  'toggle-component-visibility': [id: string]
  'toggle-component-lock': [id: string]
}>()

// ─── 分类数据 ────────────────────────────────────

interface PanelCategory {
  key: string
  label: string
  items: typeof COMPONENT_DEFINITIONS
}

const categories = computed<PanelCategory[]>(() => {
  const categoryMap: Record<string, string> = {
    border: '边框装饰',
    metric: '指标卡片',
    chart: '图表',
    video: '视频',
    text: '文本',
  }

  const map: Record<string, typeof COMPONENT_DEFINITIONS> = {}
  for (const def of COMPONENT_DEFINITIONS) {
    if (!map[def.category]) map[def.category] = []
    map[def.category].push(def)
  }

  return Object.entries(map).map(([key, items]) => ({
    key,
    label: categoryMap[key] || key,
    items,
  }))
})

// 展开/折叠
const expandedCategories = ref<Set<string>>(new Set(['border', 'metric', 'chart', 'video', 'text']))

function toggleCategory(key: string) {
  if (expandedCategories.value.has(key)) {
    expandedCategories.value.delete(key)
  } else {
    expandedCategories.value.add(key)
  }
}

// ─── 组件图标映射 ────────────────────────────────

function getCategoryIcon(category: string): string {
  const icons: Record<string, string> = {
    border: 'square',
    metric: 'hash',
    chart: 'bar-chart-2',
    video: 'video',
    text: 'type',
  }
  return icons[category] || 'box'
}

// ─── 拖拽 ───────────────────────────────────────

function handleDragStart(event: DragEvent, type: ComponentType) {
  if (!event.dataTransfer) return
  event.dataTransfer.setData('application/x-component-type', type)
  event.dataTransfer.effectAllowed = 'copy'
}

// ─── 图层面板事件转发 ──────────────────────────

function handleLayerSelect(id: string | null) {
  emit('select-component', id)
}

function handleLayerBringToFront(id: string) {
  emit('bring-to-front', id)
}

function handleLayerMoveUp(id: string) {
  emit('move-layer-up', id)
}

function handleLayerMoveDown(id: string) {
  emit('move-layer-down', id)
}

function handleLayerMoveToBottom(id: string) {
  emit('move-layer-to-bottom', id)
}

function handleLayerToggleVisibility(id: string) {
  emit('toggle-component-visibility', id)
}

function handleLayerToggleLock(id: string) {
  emit('toggle-component-lock', id)
}
</script>

<template>
  <div class="component-panel w-[260px] flex flex-col bg-[#0a192f] border-r border-[#1e293b] flex-shrink-0">
    <!-- 上半部：组件列表 -->
    <div class="flex-1 overflow-y-auto">
      <div class="h-12 flex items-center px-4 border-b border-[#1e293b]">
        <span class="text-sm font-semibold text-white">组件</span>
      </div>

      <!-- 分类 -->
      <div class="p-3 space-y-2">
        <div
          v-for="cat in categories"
          :key="cat.key"
          class="space-y-1"
        >
          <!-- 分类标题 -->
          <button
            class="w-full flex items-center justify-between px-2 py-1.5 rounded-md text-xs text-[#8892a0] hover:text-white hover:bg-[#112240] cursor-pointer transition-colors"
            @click="toggleCategory(cat.key)"
          >
            <span class="font-medium">{{ cat.label }}</span>
            <svg
              class="w-3.5 h-3.5 transition-transform duration-200"
              :class="{ 'rotate-90': expandedCategories.has(cat.key) }"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </button>

          <!-- 组件条目 -->
          <div v-if="expandedCategories.has(cat.key)" class="space-y-1 pl-1">
            <div
              v-for="item in cat.items"
              :key="item.type"
              class="group flex items-center gap-3 px-2.5 py-2 rounded-md bg-[#112240] border border-[#1e293b] hover:border-[#00d9ff]/30 hover:bg-[#172a45] cursor-pointer transition-all"
              draggable="true"
              @dragstart="handleDragStart($event, item.type)"
              @click="emit('add-component-by-click', item.type)"
            >
              <!-- 图标 -->
              <div class="w-8 h-8 rounded-md bg-[#0a192f] flex items-center justify-center border border-[#1e293b] group-hover:border-[#00d9ff]/20">
                <svg
                  v-if="item.icon === 'square'"
                  class="w-4 h-4 text-[#4a9eff]"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <rect x="3" y="3" width="18" height="18" rx="2" />
                </svg>
                <svg
                  v-else-if="item.icon === 'sparkles'"
                  class="w-4 h-4 text-[#a855f7]"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3z" />
                </svg>
                <svg
                  v-else-if="item.icon === 'credit-card'"
                  class="w-4 h-4 text-[#00d9ff]"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <rect x="1" y="4" width="22" height="16" rx="2" />
                  <line x1="1" y1="10" x2="23" y2="10" />
                </svg>
                <svg
                  v-else-if="item.icon === 'hash'"
                  class="w-4 h-4 text-[#00ff88]"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <line x1="4" y1="9" x2="20" y2="9" />
                  <line x1="4" y1="15" x2="20" y2="15" />
                  <line x1="10" y1="3" x2="8" y2="21" />
                  <line x1="16" y1="3" x2="14" y2="21" />
                </svg>
                <svg
                  v-else-if="item.icon === 'trending-up'"
                  class="w-4 h-4 text-[#f97316]"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
                  <polyline points="17 6 23 6 23 12" />
                </svg>
                <svg
                  v-else-if="item.icon === 'bar-chart-2'"
                  class="w-4 h-4 text-[#f43f5e]"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <line x1="18" y1="20" x2="18" y2="10" />
                  <line x1="12" y1="20" x2="12" y2="4" />
                  <line x1="6" y1="20" x2="6" y2="14" />
                </svg>
                <svg
                  v-else-if="item.icon === 'video'"
                  class="w-4 h-4 text-[#06b6d4]"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <polygon points="23 7 16 12 23 17 23 7" />
                  <rect x="1" y="5" width="15" height="14" rx="2" />
                </svg>
                <svg
                  v-else-if="item.icon === 'type'"
                  class="w-4 h-4 text-[#10b981]"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <polyline points="4 7 4 4 20 4 20 7" />
                  <line x1="9" y1="20" x2="15" y2="20" />
                  <line x1="12" y1="4" x2="12" y2="20" />
                </svg>
                <svg
                  v-else-if="item.icon === 'file-text'"
                  class="w-4 h-4 text-[#a855f7]"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                  <polyline points="10 9 9 9 8 9" />
                </svg>
                <svg
                  v-else-if="item.icon === 'clock'"
                  class="w-4 h-4 text-[#3b82f6]"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
                <svg
                  v-else
                  class="w-4 h-4 text-[#8892a0]"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <box :key="item.icon" />
                </svg>
              </div>

              <!-- 名称和尺寸 -->
              <div class="flex-1 min-w-0">
                <p class="text-xs font-medium text-white truncate">{{ item.name }}</p>
                <p class="text-[10px] text-[#5a6a80] mt-0.5">
                  {{ item.defaultSize.width }} × {{ item.defaultSize.height }}
                </p>
              </div>

              <!-- 拖拽提示 -->
              <div class="opacity-0 group-hover:opacity-100 transition-opacity">
                <svg class="w-3.5 h-3.5 text-[#00d9ff]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="9" cy="5" r="1" />
                  <circle cx="15" cy="5" r="1" />
                  <circle cx="9" cy="12" r="1" />
                  <circle cx="15" cy="12" r="1" />
                  <circle cx="9" cy="19" r="1" />
                  <circle cx="15" cy="19" r="1" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 分隔线 -->
    <div class="h-px bg-[#1e293b]" />

    <!-- 下半部：图层面板 -->
    <LayerPanel
      :components="components"
      :selected-component-id="selectedComponentId"
      @select-component="handleLayerSelect"
      @bring-to-front="handleLayerBringToFront"
      @move-layer-up="handleLayerMoveUp"
      @move-layer-down="handleLayerMoveDown"
      @move-layer-to-bottom="handleLayerMoveToBottom"
      @toggle-component-visibility="handleLayerToggleVisibility"
      @toggle-component-lock="handleLayerToggleLock"
    />
  </div>
</template>

<style scoped>
.component-panel {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.component-panel::-webkit-scrollbar {
  width: 4px;
}

.component-panel::-webkit-scrollbar-track {
  background: transparent;
}

.component-panel::-webkit-scrollbar-thumb {
  background: #1e293b;
  border-radius: 2px;
}
</style>
