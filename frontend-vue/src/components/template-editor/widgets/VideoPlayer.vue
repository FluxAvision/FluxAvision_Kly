<script setup lang="ts">
/**
 * 视频播放器组件
 */
import { computed } from 'vue'
import { Wifi, WifiOff } from 'lucide-vue-next'
import RTSPVideoPlayer from '@/components/video/RTSPVideoPlayer.vue'
import type { ComponentConfig } from '@/types/template-editor'
import type { Device } from '@/components/large-screen/composables/useLargeScreenData'

const props = defineProps<{
  config: ComponentConfig
  data?: { device?: Device }
}>()

const device = computed(() => props.data?.device)
const showName = computed(() => props.config.props?.showName ?? true)
const autoPlay = computed(() => props.config.props?.autoPlay ?? true)
</script>

<template>
  <div class="w-full h-full bg-black/40 border border-white/10 rounded-lg overflow-hidden flex flex-col">
    <!-- 设备名称 -->
    <div
      v-if="showName && device"
      class="flex items-center gap-2 px-3 py-1.5 bg-black/30 flex-shrink-0"
    >
      <Wifi v-if="device.status === 'online'" class="w-3 h-3 text-[#00ff88]" />
      <WifiOff v-else class="w-3 h-3 text-[#ef4444]" />
      <span class="text-xs text-white truncate">{{ device.name }}</span>
    </div>

    <!-- 视频区域 -->
    <div class="flex-1 min-h-0">
      <RTSPVideoPlayer
        v-if="device"
        :device-id="device.id"
        :name="device.name"
        :status="device.status"
        :auto-play="autoPlay"
        :compact="true"
        :show-controls="false"
        class="w-full h-full"
      />
      <div v-else class="w-full h-full flex items-center justify-center text-[#8892a0] text-sm">
        请绑定设备
      </div>
    </div>
  </div>
</template>
