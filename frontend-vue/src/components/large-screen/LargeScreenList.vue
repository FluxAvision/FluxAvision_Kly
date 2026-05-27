<script setup lang="ts">
/**
 * 大屏模板列表 - LargeScreenList.vue
 *
 * 全部模板均为自定义模板，预置模板由后端数据库初始化
 */
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { fetchTemplates, deleteTemplate } from '@/services/largeScreenApi'
import type { ScreenTemplateItem } from '@/services/largeScreenApi'

const templates = ref<ScreenTemplateItem[]>([])
const loading = ref(true)
const deleting = ref(false)

// 默认模板ID（从localStorage读取，实时响应）
const defaultTemplateId = ref(localStorage.getItem('defaultTemplateId') || '')

onMounted(() => { loadTemplates() })

async function loadTemplates() {
  loading.value = true
  try {
    templates.value = await fetchTemplates()
  } catch (e: any) {
    message.error(e.message || '加载模板列表失败')
  } finally {
    loading.value = false
  }
}

function setDefaultTemplate(tplId: string, tplName: string) {
  localStorage.setItem('defaultTemplateId', tplId)
  localStorage.setItem('defaultTemplateName', tplName)
  defaultTemplateId.value = tplId
  message.success(`已设为默认模板: ${tplName}`)
}

function handleCreate() {
  window.open('/large-screen-designer.html', '_blank')
}

function handlePreview(tpl: ScreenTemplateItem) {
  window.open(`/large-screen.html?templateId=${tpl.id}`, '_blank')
}

function handleEdit(tpl: ScreenTemplateItem) {
  window.open(`/large-screen-designer.html?templateId=${tpl.id}`, '_blank')
}

async function handleDelete(tpl: ScreenTemplateItem) {
  if (!confirm(`确定删除模板「${tpl.name}」吗？此操作不可撤销。`)) return
  deleting.value = true
  try {
    await deleteTemplate(tpl.id)
    message.success('模板已删除')
    await loadTemplates()
  } catch (e: any) {
    message.error(e.message || '删除失败')
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="rounded-xl border border-[#1e293b] bg-[#112240] p-6">
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-3">
        <h2 class="text-lg font-medium text-white">大屏模板</h2>
        <span class="text-sm text-[#8892a0]">创建和管理大屏显示模板，点击模板开始编辑</span>
      </div>
      <button
        class="rounded-md bg-[#00d9ff] px-4 py-2 text-sm font-medium text-[#0a192f] hover:bg-[#00d9ff]/80 transition-colors cursor-pointer"
        @click="handleCreate"
      >
        + 新建模板
      </button>
    </div>

    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="i in 3" :key="i" class="rounded-xl border border-[#1e293b] bg-[#0a192f] p-4 space-y-3">
        <div class="w-full h-24 rounded-lg bg-[#1e293b] animate-pulse" />
        <div class="h-4 w-24 bg-[#1e293b] rounded animate-pulse" />
        <div class="h-3 w-full bg-[#1e293b] rounded animate-pulse" />
      </div>
    </div>

    <div v-else>
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-medium text-[#8892a0]">全部模板</h3>
        <span class="text-xs text-[#5a6a80]">{{ templates.length }} 个模板</span>
      </div>

      <div v-if="templates.length === 0" class="rounded-xl border border-dashed border-[#1e293b] bg-[#0a192f] p-8 text-center">
        <svg class="w-12 h-12 mx-auto mb-3 text-[#1e293b]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="12" y1="18" x2="12" y2="12" />
          <line x1="9" y1="15" x2="15" y2="15" />
        </svg>
        <p class="text-sm text-[#8892a0]">暂无模板</p>
        <p class="text-xs text-[#5a6a80] mt-1">点击右上角"新建模板"创建</p>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          v-for="tpl in templates"
          :key="tpl.id"
          class="rounded-xl border transition-all duration-200 hover:scale-[1.02] group relative"
          :class="tpl.id === defaultTemplateId ? 'border-[#00d9ff] bg-[#0a192f]' : 'border-[#1e293b] bg-[#0a192f]'"
        >
          <!-- 默认角标 -->
          <div v-if="tpl.id === defaultTemplateId"
            class="absolute -top-px -left-px z-10 px-2 py-0.5 rounded-tl-xl rounded-br-md text-[10px] font-semibold bg-[#00d9ff] text-[#0a192f]">
            默认
          </div>
          <div class="p-4">
            <div class="w-full h-24 rounded-lg mb-3 flex items-center justify-center overflow-hidden" @click="handleEdit(tpl)">
              <svg class="w-8 h-8 text-[#1e293b] group-hover:text-[#00d9ff]/50 transition-colors" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <rect x="2" y="3" width="20" height="14" rx="2" /><line x1="8" y1="21" x2="16" y2="21" /><line x1="12" y1="17" x2="12" y2="21" />
              </svg>
            </div>
            <div class="flex items-start justify-between" @click="handleEdit(tpl)">
              <div class="flex-1 min-w-0">
                <h4 class="text-sm font-medium text-white truncate">{{ tpl.name }}</h4>
                <p class="text-xs text-[#8892a0] mt-1 truncate">{{ tpl.description || tpl.canvasWidth + '×' + tpl.canvasHeight || '' }}</p>
                <div class="flex items-center gap-2 mt-1.5">
                  <span class="text-[10px] text-[#5a6a80]">{{ tpl.canvasWidth }}×{{ tpl.canvasHeight }}</span>
                  <span class="text-[#1e293b]">·</span>
                  <span class="text-[10px] text-[#5a6a80]">{{ tpl.updatedAt ? new Date(tpl.updatedAt).toLocaleDateString() : '' }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="flex items-center gap-1 absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <button class="px-2 py-1 rounded text-[10px] bg-[#00d9ff]/20 text-[#00d9ff] border border-[#00d9ff]/30 hover:bg-[#00d9ff]/30 cursor-pointer transition-colors" @click.stop="setDefaultTemplate(tpl.id, tpl.name)">
              默认
            </button>
            <button class="px-2 py-1 rounded text-[10px] bg-[#172a45] text-[#ccd6f6] border border-[#1e293b] hover:bg-[#1e293b] cursor-pointer transition-colors" title="预览" @click.stop="handlePreview(tpl)">
              预览
            </button>
            <button class="p-1.5 rounded hover:bg-[#1e293b] text-[#8892a0] hover:text-white transition-colors cursor-pointer" title="编辑" @click.stop="handleEdit(tpl)">
              <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" /></svg>
            </button>
            <button :disabled="deleting" class="p-1.5 rounded hover:bg-[#1e293b] text-[#8892a0] hover:text-[#ef4444] transition-colors cursor-pointer disabled:opacity-30" title="删除" @click.stop="handleDelete(tpl)">
              <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" /></svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
