<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { Clock } from 'lucide-vue-next'

defineProps<{
  title: string
  storeName?: string
}>()

const currentTime = ref('')
let interval: ReturnType<typeof setInterval> | null = null

function update() {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
}

onMounted(() => {
  update()
  interval = setInterval(update, 1000)
})

onUnmounted(() => {
  if (interval) clearInterval(interval)
})
</script>

<template>
  <header class="h-16 bg-[#0a192f] border-b border-[#1e293b] flex items-center justify-between px-6 flex-shrink-0">
    <!-- Left: Breadcrumb -->
    <div class="flex items-center gap-2 text-sm">
      <span class="text-[#8892a0]">首页</span>
      <span class="text-[#8892a0]">/</span>
      <span class="text-white font-medium">{{ title }}</span>
    </div>

    <!-- Right: Store name + Time -->
    <div class="flex items-center gap-4">
      <span
        v-if="storeName"
        class="text-xs bg-[#172a45] text-[#00d9ff] px-3 py-1 rounded-full border border-[#1e293b]"
      >
        {{ storeName }}
      </span>
      <div class="flex items-center gap-2 text-sm text-[#8892a0]">
        <Clock class="w-4 h-4" />
        <span>{{ currentTime }}</span>
      </div>
    </div>
  </header>
</template>
