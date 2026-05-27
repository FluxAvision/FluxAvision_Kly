<script setup lang="ts">
/**
 * 图层面板 - LayerPanel.vue
 *
 * 显示画布中所有组件按 zIndex 降序排列（最上层显示在最顶部）
 * 功能：
 * - 单击选中图层
 * - 切换可见性（眼睛图标）
 * - 切换锁定（锁图标）
 * - 层级操作：置顶、上移、下移、置底
 */
import { computed, ref } from 'vue'
import type { ComponentConfig } from '@/types/template-editor'

const props = defineProps<{
  components: ComponentConfig[]
  selectedComponentId: string | null
}>()

const emit = defineEmits<{
  'select-component': [id: string | null]
  'bring-to-front': [id: string]
  'move-layer-up': [id: string]
  'move-layer-down': [id: string]
  'move-layer-to-bottom': [id: string]
  'toggle-component-visibility': [id: string]
  'toggle-component-lock': [id: string]
}>()

// ─── 排序：zIndex 降序（最上层显示在最上面）──────

const sortedLayers = computed(() => {
  return [...props.components].sort((a, b) => b.zIndex - a.zIndex)
})

// ─── 搜索过滤 ──────────────────────────────────

const searchQuery = ref('')

const filteredLayers = computed(() => {
  if (!searchQuery.value.trim()) return sortedLayers.value
  const q = searchQuery.value.toLowerCase().trim()
  return sortedLayers.value.filter(c => c.name.toLowerCase().includes(q) || c.type.toLowerCase().includes(q))
})

// ─── 类型图标 ──────────────────────────────────

function getTypeIcon(type: string): string {
  const icons: Record<string, string> = {
    border: '⬜',
    decoration: '✨',
    'metric-card': '📊',
    counter: '🔢',
    'chart-line': '📈',
    'chart-bar': '📊',
    video: '🎥',
    title: '📝',
    text: '📄',
    clock: '🕐',
  }
  return icons[type] || '📦'
}

// ─── 选中 ─────────────────────────────────────

function handleSelect(id: string | null) {
  emit('select-component', id)
}
</script>

<template>
  <div class="layer-panel flex flex-col bg-[#0a192f] h-full">
    <!-- 标题栏 -->
    <div class="h-12 flex items-center justify-between px-4 border-b border-[#1e293b]">
      <span class="text-sm font-semibold text-white">图层</span>
      <span class="text-xs text-[#5a6a80]">{{ components.length }} 层</span>
    </div>

    <!-- 搜索框 -->
    <div class="px-3 py-2 border-b border-[#1e293b]">
      <div class="relative">
        <svg
          class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#5a6a80]"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          class="w-full h-8 pl-8 pr-3 rounded-md bg-[#112240] border border-[#1e293b] text-xs text-white outline-none placeholder:text-[#5a6a80] focus:border-[#00d9ff] transition-colors"
          placeholder="搜索图层..."
        />
      </div>
    </div>

    <!-- 图层列表 -->
    <div class="flex-1 overflow-y-auto">
      <div
        v-if="filteredLayers.length === 0"
        class="flex flex-col items-center justify-center py-8 text-center"
      >
        <svg class="w-8 h-8 text-[#1e293b] mb-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M12 2L2 7l10 5 10-5-10-5z" />
          <path d="M2 17l10 5 10-5" />
          <path d="M2 12l10 5 10-5" />
        </svg>
        <p class="text-xs text-[#5a6a80]">暂无图层</p>
        <p class="text-[10px] text-[#5a6a80] mt-0.5">添加组件后将在此显示</p>
      </div>

      <div
        v-for="(comp, index) in filteredLayers"
        :key="comp.id"
        class="group flex items-center gap-2 px-3 py-2 border-b border-[#1e293b]/50 cursor-pointer transition-colors"
        :class="[
          selectedComponentId === comp.id
            ? 'bg-[#172a45] border-l-2 border-l-[#00d9ff]'
            : 'hover:bg-[#112240] border-l-2 border-l-transparent'
        ]"
        @click="handleSelect(comp.id)"
      >
        <!-- 序号 -->
        <span class="text-[10px] text-[#5a6a80] w-4 flex-shrink-0 text-right">
          {{ filteredLayers.length - index }}
        </span>

        <!-- 类型图标 -->
        <span class="text-xs flex-shrink-0">{{ getTypeIcon(comp.type) }}</span>

        <!-- 名称 -->
        <span
          class="flex-1 text-xs truncate min-w-0"
          :class="selectedComponentId === comp.id ? 'text-[#00d9ff]' : 'text-[#ccd6f6]'"
        >
          {{ comp.name }}
        </span>

        <!-- 操作按钮 -->
        <div class="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
          <!-- 可见性 -->
          <button
            class="w-6 h-6 flex items-center justify-center rounded hover:bg-[#1e293b] cursor-pointer transition-colors"
            :title="comp.visible ? '隐藏' : '显示'"
            @click.stop="emit('toggle-component-visibility', comp.id)"
          >
            <svg
              v-if="comp.visible"
              class="w-3.5 h-3.5 text-[#8892a0]"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
            <svg
              v-else
              class="w-3.5 h-3.5 text-[#5a6a80]"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94" />
              <path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19" />
              <line x1="1" y1="1" x2="23" y2="23" />
            </svg>
          </button>

          <!-- 锁定 -->
          <button
            class="w-6 h-6 flex items-center justify-center rounded hover:bg-[#1e293b] cursor-pointer transition-colors"
            :title="comp.locked ? '解锁' : '锁定'"
            @click.stop="emit('toggle-component-lock', comp.id)"
          >
            <svg
              v-if="comp.locked"
              class="w-3.5 h-3.5 text-[#f43f5e]"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <rect x="3" y="11" width="18" height="11" rx="2" />
              <path d="M7 11V7a5 5 0 0110 0v4" />
            </svg>
            <svg
              v-else
              class="w-3.5 h-3.5 text-[#8892a0]"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <rect x="3" y="11" width="18" height="11" rx="2" />
              <path d="M7 11V7a5 5 0 0110 0v4" />
              <circle cx="12" cy="16" r="1" fill="currentColor" />
            </svg>
          </button>
        </div>

        <!-- 层级操作（选中时显示完整层级菜单） -->
        <div
          v-if="selectedComponentId === comp.id"
          class="flex items-center gap-0.5 flex-shrink-0"
        >
          <!-- 置顶 -->
          <button
            class="w-6 h-6 flex items-center justify-center rounded hover:bg-[#1e293b] cursor-pointer transition-colors"
            title="置顶"
            @click.stop="emit('bring-to-front', comp.id)"
          >
            <svg class="w-3 h-3 text-[#00d9ff]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="18 15 12 9 6 15" />
            </svg>
          </button>

          <!-- 上移 -->
          <button
            class="w-6 h-6 flex items-center justify-center rounded hover:bg-[#1e293b] cursor-pointer transition-colors"
            title="上移一层"
            @click.stop="emit('move-layer-up', comp.id)"
          >
            <svg class="w-3 h-3 text-[#8892a0]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="18 15 12 9 6 15" />
              <line x1="12" y1="3" x2="12" y2="21" />
            </svg>
          </button>

          <!-- 下移 -->
          <button
            class="w-6 h-6 flex items-center justify-center rounded hover:bg-[#1e293b] cursor-pointer transition-colors"
            title="下移一层"
            @click.stop="emit('move-layer-down', comp.id)"
          >
            <svg class="w-3 h-3 text-[#8892a0]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 12 15 18 9" />
              <line x1="12" y1="3" x2="12" y2="21" />
            </svg>
          </button>

          <!-- 置底 -->
          <button
            class="w-6 h-6 flex items-center justify-center rounded hover:bg-[#1e293b] cursor-pointer transition-colors"
            title="置底"
            @click.stop="emit('move-layer-to-bottom', comp.id)"
          >
            <svg class="w-3 h-3 text-[#8892a0]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.layer-panel {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  min-height: 0;
}

.layer-panel::-webkit-scrollbar {
  width: 4px;
}

.layer-panel::-webkit-scrollbar-track {
  background: transparent;
}

.layer-panel::-webkit-scrollbar-thumb {
  background: #1e293b;
  border-radius: 2px;
}
</style>
