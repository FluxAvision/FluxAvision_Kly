<script setup lang="ts">
import {
  LayoutDashboard,
  Camera,
  BarChart3,
  Settings,
  Monitor,
  Presentation,
} from 'lucide-vue-next'
import { markRaw, type Component } from 'vue'

defineProps<{
  activePage: string
}>()

const emit = defineEmits<{
  pageChange: [page: string]
  navigateToScreen: []
}>()

interface NavItem {
  id: string
  label: string
  icon: Component
}

const navItems: NavItem[] = [
  { id: 'dashboard', label: '仪表盘', icon: markRaw(LayoutDashboard) },
  { id: 'devices', label: '设备管理', icon: markRaw(Camera) },
  { id: 'history', label: '历史数据', icon: markRaw(BarChart3) },
]

const settingsItems: NavItem[] = [
  { id: 'settings', label: '系统设置', icon: markRaw(Settings) },
  { id: 'large-screen-settings', label: '大屏设置', icon: markRaw(Presentation) },
]
</script>

<template>
  <aside class="fixed left-0 top-0 bottom-0 w-[240px] bg-[#0a192f] border-r border-[#1e293b] flex flex-col z-50">
    <!-- Logo -->
    <div class="flex items-center gap-3 px-6 h-16 border-b border-[#1e293b] flex-shrink-0">
      <img src="/logo.png" alt="FluxaVision" class="w-8 h-8 rounded-lg" />
      <span class="text-lg font-bold text-white tracking-wide">FluxAvision</span>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
      <p class="px-3 py-1.5 text-xs text-[#8892a0]/60 font-medium uppercase tracking-wider">
        数据概览
      </p>
      <button
        v-for="item in navItems"
        :key="item.id"
        class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer"
        :class="[
          activePage === item.id
            ? 'sidebar-active-indicator bg-[#172a45] text-[#00d9ff]'
            : 'text-[#8892a0] hover:bg-[#172a45] hover:text-white'
        ]"
        @click="emit('pageChange', item.id)"
      >
        <component :is="item.icon" class="w-5 h-5 flex-shrink-0" />
        <span>{{ item.label }}</span>
      </button>

      <div class="my-3 mx-3 border-t border-[#1e293b]" />

      <p class="px-3 py-1.5 text-xs text-[#8892a0]/60 font-medium uppercase tracking-wider">
        系统管理
      </p>
      <button
        v-for="item in settingsItems"
        :key="item.id"
        class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer"
        :class="[
          activePage === item.id
            ? 'sidebar-active-indicator bg-[#172a45] text-[#00d9ff]'
            : 'text-[#8892a0] hover:bg-[#172a45] hover:text-white'
        ]"
        @click="emit('pageChange', item.id)"
      >
        <component :is="item.icon" class="w-5 h-5 flex-shrink-0" />
        <span>{{ item.label }}</span>
      </button>
    </nav>

    <!-- Large Screen Button -->
    <div class="px-3 pb-2 flex-shrink-0">
      <button
        class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-[#8892a0] hover:bg-[#172a45] hover:text-white transition-all duration-200 cursor-pointer border border-dashed border-[#1e293b] hover:border-[#00d9ff]/30"
        @click="emit('navigateToScreen')"
      >
        <Monitor class="w-5 h-5 flex-shrink-0" />
        <span>大屏模式</span>
      </button>
    </div>

    <!-- Version -->
    <div class="px-6 pb-4 flex-shrink-0">
      <p class="text-xs text-[#8892a0]/50">FluxAvision v2.1.0</p>
    </div>
  </aside>
</template>
