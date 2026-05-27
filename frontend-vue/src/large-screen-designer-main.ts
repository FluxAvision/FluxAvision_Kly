/**
 * 大屏设计器入口
 *
 * 独立的全屏编辑页面
 * 支持 URL 参数 ?templateId=xxx 加载已有模板
 * 无参数则创建空模板
 */
import { createApp, ref, onMounted, defineComponent, h } from 'vue'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import DataVVue3 from '@kjgl77/datav-vue3'
import LargeScreenDesigner from './components/large-screen/designer/LargeScreenDesigner.vue'
import { fetchTemplateDetail } from './services/largeScreenApi'
import { parseTemplateConfig } from './types/template-editor'
import './assets/main.css'

// ─── 加载层组件 ──────────────────────────────────────────

const AppWithLoading = defineComponent({
  setup() {
    const loading = ref(true)
    const error = ref('')
    const designerRef = ref<InstanceType<typeof LargeScreenDesigner> | null>(null)

    onMounted(async () => {
      const params = new URLSearchParams(window.location.search)
      const templateId = params.get('templateId')

      if (templateId) {
        try {
          const detail = await fetchTemplateDetail(templateId)
          if (detail) {
            const config = parseTemplateConfig(detail.templateConfig)
            const appEl = document.getElementById('app')
            if (appEl) {
              appEl.dataset.templateId = templateId
              appEl.dataset.templateName = detail.name
              appEl.dataset.templateConfig = JSON.stringify(config)
            }
          } else {
            error.value = '模板不存在'
          }
        } catch (e: any) {
          error.value = `加载模板失败: ${e.message}`
        }
      }

      loading.value = false
    })

    return () => {
      if (loading.value) {
        return h('div', {
          class: 'h-screen bg-[#0a192f] flex items-center justify-center',
        }, [
          h('div', { class: 'text-center' }, [
            h('div', { class: 'w-8 h-8 border-2 border-[#00d9ff] border-t-transparent rounded-full animate-spin mx-auto mb-3' }),
            h('div', { class: 'text-sm text-[#8892a0]' }, '加载模板中...'),
          ]),
        ])
      }

      if (error.value) {
        return h('div', {
          class: 'h-screen bg-[#0a192f] flex flex-col items-center justify-center',
        }, [
          h('div', { class: 'text-[#ef4444] text-lg mb-2' }, '加载失败'),
          h('div', { class: 'text-sm text-[#8892a0] mb-4' }, error.value),
          h('button', {
            class: 'px-4 py-2 bg-[#00d9ff] text-[#0a192f] rounded-lg text-sm font-medium cursor-pointer hover:bg-[#00d9ff]/90 transition-colors',
            onClick: () => { window.close() },
          }, '关闭'),
        ])
      }

      return h(LargeScreenDesigner)
    }
  },
})

const app = createApp(AppWithLoading)
app.use(Antd)
app.use(DataVVue3)
app.mount('#app')
