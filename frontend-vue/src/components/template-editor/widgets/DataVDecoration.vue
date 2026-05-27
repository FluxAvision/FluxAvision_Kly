<script setup lang="ts">
/**
 * DataV 装饰组件 — ResizeObserver + :key 强制重渲染
 *
 * DataV Decoration 内部渲染固定尺寸的 SVG，在 onMounted 时计算尺寸后不再更新。
 * 通过 ResizeObserver 监听容器尺寸变化，递增 wrapKey 强制销毁重建 DataV 组件，
 * 使其重新计算 SVG 尺寸适应新容器大小。
 */
import { computed, ref, onMounted, onUnmounted } from 'vue'
import type { ComponentConfig } from '@/types/template-editor'

const props = defineProps<{
  config: ComponentConfig
  data?: any
}>()

const decorationType = computed(() => props.config.props?.decorationType || 'dv-decoration-1')

// 装饰线颜色（DataV Decoration 也支持 color: string[]）
const decorationColors = computed(() => {
  const colors = props.config.props?.decorationColors
  return Array.isArray(colors) && colors.length > 0 ? colors : undefined
})

// ─── 尺寸监听——强制重渲染 ─────────────────────

const wrapperRef = ref<HTMLElement | null>(null)
const wrapKey = ref(0)

let resizeObserver: ResizeObserver | null = null

function updateKey() {
  wrapKey.value++
}

onMounted(() => {
  resizeObserver = new ResizeObserver(updateKey)
  if (wrapperRef.value) resizeObserver.observe(wrapperRef.value)
})

onUnmounted(() => {
  resizeObserver?.disconnect()
})
</script>

<template>
  <div ref="wrapperRef" class="w-full h-full overflow-hidden">
    <dv-decoration-1 v-if="decorationType === 'dv-decoration-1'" :key="wrapKey" class="w-full h-full" :color="decorationColors" />
    <dv-decoration-2 v-else-if="decorationType === 'dv-decoration-2'" :key="wrapKey" class="w-full h-full" :color="decorationColors" />
    <dv-decoration-3 v-else-if="decorationType === 'dv-decoration-3'" :key="wrapKey" class="w-full h-full" :color="decorationColors" />
    <dv-decoration-4 v-else-if="decorationType === 'dv-decoration-4'" :key="wrapKey" class="w-full h-full" :color="decorationColors" />
    <dv-decoration-5 v-else-if="decorationType === 'dv-decoration-5'" :key="wrapKey" class="w-full h-full" :color="decorationColors" />
    <dv-decoration-6 v-else-if="decorationType === 'dv-decoration-6'" :key="wrapKey" class="w-full h-full" :color="decorationColors" />
    <dv-decoration-7 v-else-if="decorationType === 'dv-decoration-7'" :key="wrapKey" class="w-full h-full" :color="decorationColors">
      {{ config.props?.text || 'Decoration' }}
    </dv-decoration-7>
    <dv-decoration-8 v-else-if="decorationType === 'dv-decoration-8'" :key="wrapKey" class="w-full h-full" :color="decorationColors" />
    <dv-decoration-9 v-else-if="decorationType === 'dv-decoration-9'" :key="wrapKey" class="w-full h-full" :color="decorationColors" />
    <dv-decoration-10 v-else-if="decorationType === 'dv-decoration-10'" :key="wrapKey" class="w-full h-full" :color="decorationColors" />
    <dv-decoration-11 v-else-if="decorationType === 'dv-decoration-11'" :key="wrapKey" class="w-full h-full" :color="decorationColors">
      {{ config.props?.text || 'Decoration' }}
    </dv-decoration-11>
    <dv-decoration-12 v-else-if="decorationType === 'dv-decoration-12'" :key="wrapKey" class="w-full h-full" :color="decorationColors" />
    <!-- 默认装饰 -->
    <div v-else class="w-full h-full border-t border-[#00d9ff]/30" />
  </div>
</template>
