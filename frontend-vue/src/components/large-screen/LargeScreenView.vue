<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import { useLargeScreenData } from './composables/useLargeScreenData'
import { parseTemplateConfig, type TemplateConfig } from '@/types/template-editor'
import GeneralTemplate from './templates/GeneralTemplate.vue'
import MinimalTemplate from './templates/MinimalTemplate.vue'
import StandardTemplate from './templates/StandardTemplate.vue'
import VideoTemplate from './templates/VideoTemplate.vue'
import TemplateRenderer from './TemplateRenderer.vue'

const emit = defineEmits<{ close: [] }>()

const data = useLargeScreenData()

// 容器背景样式（内置模板使用通用配置，二选一）
const containerBgStyle = computed(() => {
  if (!isBuiltinTemplate.value) return {}
  const cfg = data.config.value
  if (cfg.backgroundImage) return {}
  if (cfg.backgroundColor) return { backgroundColor: cfg.backgroundColor }
  return { backgroundColor: isMinimal.value ? '#0a192f' : '#0a1a3a' }
})

// 自定义模板配置
const customTemplateConfig = ref<TemplateConfig | null>(null)
const loadingTemplate = ref(false)

// 判断是否为内置模板
const isBuiltinTemplate = computed(() => {
  const tid = data.config.value.templateId
  return tid === 'tpl-general' || tid === 'tpl-minimal' || tid === 'tpl-standard' || tid === 'tpl-video' || !tid
})

const isMinimal = computed(() => data.config.value.templateId === 'tpl-minimal')
const isStandard = computed(() => data.config.value.templateId === 'tpl-standard')

// 加载自定义模板
async function loadCustomTemplate() {
  const tid = data.config.value.templateId
  if (!tid || isBuiltinTemplate.value) {
    customTemplateConfig.value = null
    return
  }

  loadingTemplate.value = true
  try {
    const res = await fetch(`/api/large-screen/templates/${tid}`)
    if (res.ok) {
      const json = await res.json()
      const templateData = json.data || json
      console.log('templateData', templateData)
      customTemplateConfig.value = parseTemplateConfig(templateData.templateConfig)
    }
  } catch {
    customTemplateConfig.value = null
  } finally {
    loadingTemplate.value = false
  }
}

// 监听模板ID变化
watch(() => data.config.value.templateId, loadCustomTemplate, { immediate: true })

// 等待数据加载
onMounted(() => {
  // 延迟加载自定义模板
  setTimeout(loadCustomTemplate, 500)
})

function handleClose() {
  emit('close')
}
</script>

<template>
  <div
    class="fixed inset-0 z-[100] overflow-hidden"
    :style="containerBgStyle"
  >
    <!-- 背景图片覆盖（内置模板 + 有背景图） -->
    <div
      v-if="isBuiltinTemplate && data.config.value.backgroundImage"
      class="absolute inset-0 bg-cover bg-center"
      :style="{ backgroundImage: `url(${data.config.value.backgroundImage})` }"
    />
    <div
      v-if="isBuiltinTemplate && data.config.value.backgroundImage"
      class="absolute inset-0 bg-black/30"
    />

    <!-- 内置模板：简约模板 -->
    <MinimalTemplate
      v-if="isBuiltinTemplate && data.config.value.templateId === 'tpl-minimal'"
      :config="data.config.value"
      :metrics="data.metrics.value"
      :hourly-data="data.hourlyData.value"
      :devices="data.devices.value"
      :store-logo="data.storeLogo.value"
      :loading="data.loading.value"
      :clock-time="data.clockTime.value"
      :get-label="data.getLabel"
      @close="handleClose"
      @refresh="data.fetchData()"
    />

    <!-- 内置模板：视频模板 -->
    <VideoTemplate
      v-if="isBuiltinTemplate && data.config.value.templateId === 'tpl-video'"
      :config="data.config.value"
      :metrics="data.metrics.value"
      :hourly-data="data.hourlyData.value"
      :devices="data.devices.value"
      :store-logo="data.storeLogo.value"
      :loading="data.loading.value"
      :clock-time="data.clockTime.value"
      :get-label="data.getLabel"
      @close="handleClose"
    />

    <!-- 内置模板：标准模板 -->
    <StandardTemplate
      v-if="isBuiltinTemplate && data.config.value.templateId === 'tpl-standard'"
      :config="data.config.value"
      :metrics="data.metrics.value"
      :hourly-data="data.hourlyData.value"
      :devices="data.devices.value"
      :store-logo="data.storeLogo.value"
      :loading="data.loading.value"
      :clock-time="data.clockTime.value"
      :get-label="data.getLabel"
      @close="handleClose"
    />

    <!-- 内置模板：通用模板（默认） -->
    <GeneralTemplate
      v-if="isBuiltinTemplate && !data.config.value.templateId || data.config.value.templateId === 'tpl-general'"
      :config="data.config.value"
      :metrics="data.metrics.value"
      :hourly-data="data.hourlyData.value"
      :devices="data.devices.value"
      :store-logo="data.storeLogo.value"
      :loading="data.loading.value"
      :clock-time="data.clockTime.value"
      :get-label="data.getLabel"
      @close="handleClose"
    />

    <!-- 自定义模板 -->
    <div v-if="customTemplateConfig" class="relative z-10 w-full h-full">
      <!-- 关闭按钮 -->
      <button
        class="absolute top-4 right-4 z-50 w-9 h-9 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-colors cursor-pointer"
        @click="handleClose"
      >
        <span class="text-xl">×</span>
      </button>

      <!-- 模板渲染器 -->
      <TemplateRenderer :config="customTemplateConfig" />
    </div>

    <!-- 加载中 -->
    <div v-if="!isBuiltinTemplate && !customTemplateConfig" class="w-full h-full flex items-center justify-center text-white">
      <div v-if="loadingTemplate" class="text-[#8892a0]">加载模板中...</div>
      <div v-else class="text-[#8892a0]">模板不存在或加载失败</div>
    </div>
  </div>
</template>
