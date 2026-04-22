<script setup lang="ts">
/**
 * 大屏展示页面根组件
 * 关闭按钮直接关闭窗口
 */
import { computed, ref, onMounted, watch } from 'vue'
import { useLargeScreenData } from './components/large-screen/composables/useLargeScreenData'
import { parseTemplateConfig, type TemplateConfig } from './types/template-editor'
import GeneralTemplate from './components/large-screen/templates/GeneralTemplate.vue'
import MinimalTemplate from './components/large-screen/templates/MinimalTemplate.vue'
import StandardTemplate from './components/large-screen/templates/StandardTemplate.vue'
import TemplateRenderer from './components/large-screen/TemplateRenderer.vue'

const data = useLargeScreenData()

// 自定义模板配置
const customTemplateConfig = ref<TemplateConfig | null>(null)
const loadingTemplate = ref(false)

// 判断是否为内置模板
const isBuiltinTemplate = computed(() => {
  const tid = data.config.value.templateId
  return tid === 'tpl-general' || tid === 'tpl-minimal' || tid === 'tpl-standard' || !tid
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
  setTimeout(loadCustomTemplate, 500)
})

// 关闭窗口
function handleClose() {
  window.close()
  // 如果 window.close() 被浏览器阻止，提示用户手动关闭
  setTimeout(() => {
    alert('请手动关闭此页面')
  }, 100)
}
</script>

<template>
  <div
    class="w-full h-screen overflow-hidden"
    :class="isMinimal ? 'bg-[#0a192f]' : 'bg-[#0a1a3a]'"
  >
    <!-- 背景图片覆盖 -->
    <div
      v-if="data.config.value.backgroundImage"
      class="absolute inset-0 bg-cover bg-center"
      :style="{ backgroundImage: `url(${data.config.value.backgroundImage})` }"
    />
    <div v-if="data.config.value.backgroundImage" class="absolute inset-0 bg-black/30" />

    <!-- 内置模板：简约模板 -->
    <MinimalTemplate
      v-if="isBuiltinTemplate && isMinimal"
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

    <!-- 内置模板：标准模板 -->
    <StandardTemplate
      v-else-if="isBuiltinTemplate && isStandard"
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

    <!-- 内置模板：通用模板 -->
    <GeneralTemplate
      v-else-if="isBuiltinTemplate && !isMinimal && !isStandard"
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
    <div v-else-if="customTemplateConfig" class="relative z-10 w-full h-full">
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
    <div v-else class="w-full h-full flex items-center justify-center text-white">
      <div v-if="loadingTemplate" class="text-[#8892a0]">加载模板中...</div>
      <div v-else class="text-[#8892a0]">模板不存在或加载失败</div>
    </div>
  </div>
</template>
