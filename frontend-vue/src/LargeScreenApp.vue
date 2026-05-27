<script setup lang="ts">
/**
 * 大屏展示页面根组件
 * 从 localStorage 读取默认模板ID，动态加载并渲染
 */
import { ref, onMounted } from 'vue'
import { useLargeScreenData } from './components/large-screen/composables/useLargeScreenData'
import { parseTemplateConfig, type TemplateConfig } from './types/template-editor'
import TemplateRenderer from './components/large-screen/TemplateRenderer.vue'

const data = useLargeScreenData()

const templateConfig = ref<TemplateConfig | null>(null)
const loading = ref(true)
const error = ref('')

// 判断是否为预览模式：URL参数 ?templateId=xxx 优先，其次 localStorage
const urlParams = new URLSearchParams(window.location.search)
const urlTemplateId = urlParams.get('templateId')
const isPreview = !!urlTemplateId || !!localStorage.getItem('previewTemplateId')

async function loadTemplate() {
  loading.value = true
  error.value = ''

  // 优先使用 URL 参数（预览/设计师预览），其次 localStorage（大屏模式）
  const tid = urlTemplateId || localStorage.getItem('previewTemplateId') || localStorage.getItem('defaultTemplateId')

  if (!tid) {
    error.value = '未设置默认模板'
    loading.value = false
    return
  }

  try {
    const res = await fetch(`/api/large-screen/templates/${tid}`)
    if (res.ok) {
      const json = await res.json()
      const templateData = json.data || json
      templateConfig.value = parseTemplateConfig(templateData.templateConfig)
    } else {
      error.value = '模板不存在'
    }
  } catch {
    error.value = '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  setTimeout(loadTemplate, 500)
})

// 关闭窗口
function handleClose() {
  window.close()
  setTimeout(() => {
    alert('请手动关闭此页面')
  }, 100)
}
</script>

<template>
  <div class="w-full h-screen overflow-hidden bg-[#0a192f]">
    <!-- 背景图片覆盖 -->
    <div
      v-if="data.config.value.backgroundImage"
      class="absolute inset-0 bg-cover bg-center"
      :style="{ backgroundImage: `url(${data.config.value.backgroundImage})` }"
    />
    <div v-if="data.config.value.backgroundImage" class="absolute inset-0 bg-black/30" />

    <!-- 加载中 -->
    <div v-if="loading" class="w-full h-full flex items-center justify-center text-[#8892a0] text-sm">
      加载模板中...
    </div>

    <!-- 渲染模板 -->
    <div v-else-if="templateConfig" class="relative z-10 w-full h-full">
      <!-- 预览提示条 -->
      <div v-if="isPreview" class="absolute top-0 left-0 right-0 z-50 h-10 bg-[#00d9ff]/10 border-b border-[#00d9ff]/30 flex items-center justify-center gap-2">
        <span class="text-xs text-[#00d9ff]">预览模式</span>
        <span class="text-xs text-[#5a6a80]">·</span>
        <span class="text-xs text-[#8892a0]">点击关闭按钮退出预览</span>
      </div>
      <button
        class="absolute top-4 right-4 z-50 w-9 h-9 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-colors cursor-pointer"
        :class="isPreview ? 'top-12' : 'top-4'"
        @click="handleClose"
      >
        <span class="text-xl">×</span>
      </button>
      <div :class="isPreview ? 'pt-10' : ''" class="w-full h-full">
        <TemplateRenderer :config="templateConfig" />
      </div>
    </div>

    <!-- 异常 -->
    <div v-else class="w-full h-full flex items-center justify-center text-[#8892a0] text-sm">
      {{ error || '加载失败' }}
    </div>
  </div>
</template>
