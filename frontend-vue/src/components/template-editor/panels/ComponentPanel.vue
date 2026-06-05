<script setup lang="ts">
/**
 * 组件面板 - 左侧组件列表
 */
import { computed } from 'vue'
import {
  Square, Sparkles, CreditCard, Hash, TrendingUp, BarChart2,
  Video, Type, FileText, Clock, Monitor,
} from 'lucide-vue-next'
import type { ComponentDefinition } from '@/types/template-editor'
import { COMPONENT_DEFINITIONS } from '@/types/template-editor'

const emit = defineEmits<{
  addComponent: [type: string]
}>()

// 图标映射
const iconMap: Record<string, any> = {
  square: Square,
  sparkles: Sparkles,
  'credit-card': CreditCard,
  hash: Hash,
  'trending-up': TrendingUp,
  'bar-chart-2': BarChart2,
  video: Video,
  type: Type,
  'file-text': FileText,
  clock: Clock,
  monitor: Monitor,
}

// 分组
const categories = [
  { key: 'border', label: '边框装饰', color: '#4a9eff' },
  { key: 'metric', label: '指标卡片', color: '#00d9ff' },
  { key: 'chart', label: '图表', color: '#00ff88' },
  { key: 'video', label: '视频', color: '#ff9500' },
  { key: 'text', label: '文本', color: '#a855f7' },
]

const groupedComponents = computed(() => {
  const groups: Record<string, ComponentDefinition[]> = {}
  for (const cat of categories) {
    groups[cat.key] = COMPONENT_DEFINITIONS.filter(d => d.category === cat.key)
  }
  return groups
})

function handleDragStart(e: DragEvent, type: string) {
  if (e.dataTransfer) {
    e.dataTransfer.setData('componentType', type)
    e.dataTransfer.effectAllowed = 'copy'
  }
}

function handleAddClick(type: string) {
  emit('addComponent', type)
}
</script>

<template>
  <div class="component-panel h-full overflow-y-auto bg-[#0a192f] border-r border-[#1e293b]">
    <div class="p-4">
      <h3 class="text-sm font-medium text-white mb-4">组件库</h3>

      <div v-for="cat in categories" :key="cat.key" class="mb-4">
        <h4 class="text-xs text-[#8892a0] mb-2 flex items-center gap-2">
          <span class="w-2 h-2 rounded-full" :style="{ backgroundColor: cat.color }" />
          {{ cat.label }}
        </h4>

        <div class="grid grid-cols-2 gap-2">
          <div
            v-for="comp in groupedComponents[cat.key]"
            :key="comp.type"
            class="p-3 rounded-lg border border-[#1e293b] bg-[#112240] hover:border-[#00d9ff]/30 cursor-pointer transition-colors group"
            draggable="true"
            @dragstart="(e) => handleDragStart(e, comp.type)"
            @click="handleAddClick(comp.type)"
          >
            <div class="flex flex-col items-center gap-1.5">
              <component
                :is="iconMap[comp.icon] || Square"
                class="w-5 h-5 text-[#8892a0] group-hover:text-[#00d9ff] transition-colors"
              />
              <span class="text-xs text-[#8892a0] group-hover:text-white transition-colors text-center">
                {{ comp.name }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
