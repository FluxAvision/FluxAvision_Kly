<script setup lang="ts">
/**
 * 底部状态栏 - StatusBar.vue
 *
 * 显示：
 * - 画布分辨率（宽 × 高）
 * - 当前缩放比例
 * - 组件总数
 * - 选中组件信息
 */
import type { ComponentConfig } from '@/types/template-editor'

const props = defineProps<{
  canvasWidth: number
  canvasHeight: number
  zoom: number
  componentCount: number
  selectedComponent: ComponentConfig | null
}>()
</script>

<template>
  <div
    class="status-bar h-8 flex items-center justify-between px-4 bg-[#112240] border-t border-[#1e293b] text-xs text-[#8892a0] select-none"
  >
    <!-- 左侧信息 -->
    <div class="flex items-center gap-4">
      <!-- 分辨率 -->
      <span class="flex items-center gap-1.5">
        <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="2" y="3" width="20" height="14" rx="2" />
          <path d="M8 21h8" />
          <path d="M12 17v4" />
        </svg>
        {{ canvasWidth }} × {{ canvasHeight }}
      </span>

      <span class="text-[#1e293b]">|</span>

      <!-- 缩放比例 -->
      <span class="flex items-center gap-1.5">
        <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8" />
          <path d="M21 21l-4.35-4.35" />
        </svg>
        缩放 {{ zoom }}%
      </span>

      <span class="text-[#1e293b]">|</span>

      <!-- 组件数量 -->
      <span class="flex items-center gap-1.5">
        <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M16 3h5v5" />
          <path d="M8 3H3v5" />
          <path d="M16 21h5v-5" />
          <path d="M8 21H3v-5" />
        </svg>
        {{ componentCount }} 个组件
      </span>
    </div>

    <!-- 右侧选中信息 -->
    <div class="flex items-center gap-4">
      <template v-if="selectedComponent">
        <span class="flex items-center gap-1.5 text-[#00d9ff]">
          <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <path d="M3 9h18" />
            <path d="M9 21V9" />
          </svg>
          已选中: {{ selectedComponent.name }}
        </span>

        <span class="text-[#1e293b]">|</span>

        <span class="font-mono">
          X:{{ selectedComponent.x }} Y:{{ selectedComponent.y }}
        </span>

        <span class="text-[#1e293b]">|</span>

        <span class="font-mono">
          W:{{ selectedComponent.width }} H:{{ selectedComponent.height }}
        </span>

        <span class="text-[#1e293b]">|</span>

        <span class="font-mono">
          Z:{{ selectedComponent.zIndex }}
        </span>

        <span v-if="selectedComponent.locked" class="text-[#f43f5e] ml-1">
          🔒
        </span>
        <span v-if="!selectedComponent.visible" class="text-[#8892a0] ml-1">
          👁️‍🗨️
        </span>
      </template>
      <span v-else class="text-[#5a6a80]">
        未选中组件 — 点击画布上的组件以选中
      </span>
    </div>
  </div>
</template>

<style scoped>
.status-bar {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}
</style>
