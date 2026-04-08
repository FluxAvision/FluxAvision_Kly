<script setup lang="ts">
/**
 * 工具栏面板 - 顶部操作按钮
 */
import { ref, watch } from 'vue'
import { Save, Eye, Undo2, Redo2, ArrowLeft, Pencil, Check, X, Image, Palette, Upload, Trash2 } from 'lucide-vue-next'

const props = defineProps<{
  canUndo: boolean
  canRedo: boolean
  saving: boolean
  hasChanges: boolean
  templateName?: string
  canvasConfig?: {
    backgroundColor?: string
    backgroundImage?: string
  }
}>()

const emit = defineEmits<{
  save: []
  preview: []
  undo: []
  redo: []
  back: []
  rename: [name: string]
  updateCanvas: [updates: { backgroundColor?: string; backgroundImage?: string }]
}>()

// 编辑状态
const isEditingName = ref(false)
const editingName = ref('')
const showBgPanel = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)

// 背景颜色
const bgColor = ref(props.canvasConfig?.backgroundColor || '#0a192f')
const bgImage = ref(props.canvasConfig?.backgroundImage || '')

// 开始编辑名称
function startEditName() {
  editingName.value = props.templateName || '未命名模板'
  isEditingName.value = true
}

// 确认名称修改
function confirmNameChange() {
  const newName = editingName.value.trim()
  if (newName && newName !== props.templateName) {
    emit('rename', newName)
  }
  isEditingName.value = false
}

// 取消名称修改
function cancelNameChange() {
  isEditingName.value = false
}

// 更新背景颜色
function updateBgColor(color: string) {
  bgColor.value = color
  emit('updateCanvas', { backgroundColor: color, backgroundImage: bgImage.value })
}

// 更新背景图片
function updateBgImage(url: string) {
  bgImage.value = url
  emit('updateCanvas', { backgroundColor: bgColor.value, backgroundImage: url })
}

// 清除背景图片
function clearBgImage() {
  bgImage.value = ''
  emit('updateCanvas', { backgroundColor: bgColor.value, backgroundImage: '' })
}

// 触发文件选择
function triggerFileInput() {
  fileInputRef.value?.click()
}

// 处理文件上传
function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  // 检查文件类型
  if (!file.type.startsWith('image/')) {
    alert('请选择图片文件')
    return
  }

  // 检查文件大小 (限制5MB)
  if (file.size > 5 * 1024 * 1024) {
    alert('图片大小不能超过5MB')
    return
  }

  // 读取文件并转换为 base64
  const reader = new FileReader()
  reader.onload = (event) => {
    const base64 = event.target?.result as string
    updateBgImage(base64)
  }
  reader.readAsDataURL(file)

  // 清空 input，允许重复选择同一文件
  input.value = ''
}

// 监听模板名称变化
watch(() => props.templateName, (newName) => {
  if (!isEditingName.value) {
    editingName.value = newName || ''
  }
}, { immediate: true })

// 监听画布配置变化
watch(() => props.canvasConfig, (config) => {
  if (config) {
    bgColor.value = config.backgroundColor || '#0a192f'
    bgImage.value = config.backgroundImage || ''
  }
}, { immediate: true, deep: true })

// 键盘事件
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    confirmNameChange()
  } else if (e.key === 'Escape') {
    cancelNameChange()
  }
}

// 预设背景颜色
const presetColors = [
  '#0a192f', '#0d1421', '#0f172a', '#1a1a2e', '#16213e',
  '#1a1a1a', '#0d0d0d', '#1e3a5f', '#0e4166', '#0b2545',
  '#1a0a2e', '#2d1b4e', '#0a2a1f', '#0a2f1a', '#2a1a0a',
]
</script>

<template>
  <div class="toolbar-panel bg-[#0a192f] border-b border-[#1e293b]">
    <!-- 主工具栏 -->
    <div class="h-12 flex items-center justify-between px-4">
      <!-- 左侧 -->
      <div class="flex items-center gap-3">
        <button
          class="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm text-[#8892a0] hover:text-white hover:bg-white/5 transition-colors cursor-pointer"
          @click="emit('back')"
        >
          <ArrowLeft class="w-4 h-4" />
          返回
        </button>
        <div class="h-5 w-px bg-[#1e293b]" />

        <!-- 模板名称（可编辑） -->
        <div class="flex items-center gap-2">
          <template v-if="isEditingName">
            <input
              v-model="editingName"
              type="text"
              class="bg-[#112240] border border-[#00d9ff] rounded px-2 py-0.5 text-sm text-white outline-none min-w-[120px] max-w-[200px]"
              placeholder="输入模板名称"
              @keydown="handleKeydown"
              autofocus
            />
            <button
              class="p-1 rounded text-[#00d9ff] hover:bg-[#00d9ff]/10 transition-colors cursor-pointer"
              @click="confirmNameChange"
            >
              <Check class="w-4 h-4" />
            </button>
            <button
              class="p-1 rounded text-[#8892a0] hover:text-white hover:bg-white/5 transition-colors cursor-pointer"
              @click="cancelNameChange"
            >
              <X class="w-4 h-4" />
            </button>
          </template>
          <template v-else>
            <span class="text-sm text-white">{{ templateName || '未命名模板' }}</span>
            <button
              class="p-1 rounded text-[#8892a0] hover:text-white hover:bg-white/5 transition-colors cursor-pointer"
              title="重命名"
              @click="startEditName"
            >
              <Pencil class="w-3.5 h-3.5" />
            </button>
          </template>
        </div>

        <span v-if="hasChanges" class="text-xs text-[#ff9500]">* 未保存</span>
      </div>

      <!-- 右侧 -->
      <div class="flex items-center gap-2">
        <!-- 背景设置按钮 -->
        <button
          class="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm text-[#8892a0] border border-[#1e293b] hover:text-white hover:border-[#00d9ff]/50 transition-colors cursor-pointer"
          :class="{ 'border-[#00d9ff] text-[#00d9ff]': showBgPanel }"
          @click="showBgPanel = !showBgPanel"
        >
          <Palette class="w-4 h-4" />
          背景
        </button>

        <div class="h-5 w-px bg-[#1e293b]" />

        <!-- 撤销/重做 -->
        <button
          class="p-2 rounded text-[#8892a0] hover:text-white hover:bg-white/5 transition-colors disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer"
          :disabled="!canUndo"
          @click="emit('undo')"
        >
          <Undo2 class="w-4 h-4" />
        </button>
        <button
          class="p-2 rounded text-[#8892a0] hover:text-white hover:bg-white/5 transition-colors disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer"
          :disabled="!canRedo"
          @click="emit('redo')"
        >
          <Redo2 class="w-4 h-4" />
        </button>

        <div class="h-5 w-px bg-[#1e293b] mx-2" />

        <!-- 预览 -->
        <button
          class="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm text-[#8892a0] border border-[#1e293b] hover:text-white hover:border-[#00d9ff]/50 transition-colors cursor-pointer"
          @click="emit('preview')"
        >
          <Eye class="w-4 h-4" />
          预览
        </button>

        <!-- 保存 -->
        <button
          class="flex items-center gap-1.5 px-4 py-1.5 rounded text-sm bg-[#00d9ff] text-[#0a192f] font-medium hover:bg-[#00d9ff]/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer"
          :disabled="saving"
          @click="emit('save')"
        >
          <Save v-if="!saving" class="w-4 h-4" />
          <span v-else class="w-4 h-4 border-2 border-[#0a192f]/30 border-t-[#0a192f] rounded-full animate-spin" />
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </div>
    </div>

    <!-- 背景设置面板 -->
    <div v-if="showBgPanel" class="border-t border-[#1e293b] px-4 py-3 bg-[#0d1421]">
      <div class="flex items-start gap-6">
        <!-- 背景颜色 -->
        <div class="space-y-2">
          <label class="text-xs text-[#8892a0]">背景颜色</label>
          <div class="flex items-center gap-2">
            <input
              type="color"
              :value="bgColor"
              class="w-10 h-8 bg-[#112240] border border-[#1e293b] rounded cursor-pointer"
              @input="(e) => updateBgColor((e.target as HTMLInputElement).value)"
            />
            <input
              type="text"
              :value="bgColor"
              class="w-24 bg-[#112240] border border-[#1e293b] rounded px-2 py-1 text-xs text-white"
              @input="(e) => updateBgColor((e.target as HTMLInputElement).value)"
            />
          </div>
          <!-- 预设颜色 -->
          <div class="flex flex-wrap gap-1 max-w-[240px]">
            <button
              v-for="color in presetColors"
              :key="color"
              class="w-5 h-5 rounded border border-[#1e293b] cursor-pointer hover:scale-110 transition-transform"
              :style="{ backgroundColor: color }"
              :class="{ 'ring-2 ring-[#00d9ff]': bgColor === color }"
              @click="updateBgColor(color)"
            />
          </div>
        </div>

        <!-- 背景图片 -->
        <div class="space-y-2 flex-1 max-w-md">
          <label class="text-xs text-[#8892a0]">背景图片</label>
          <input
            ref="fileInputRef"
            type="file"
            accept="image/*"
            class="hidden"
            @change="handleFileSelect"
          />
          <div class="flex items-center gap-2">
            <button
              class="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm text-[#8892a0] border border-[#1e293b] hover:text-white hover:border-[#00d9ff]/50 transition-colors cursor-pointer"
              @click="triggerFileInput"
            >
              <Upload class="w-4 h-4" />
              选择图片
            </button>
            <button
              v-if="bgImage"
              class="flex items-center gap-1.5 px-2 py-1.5 rounded text-xs text-[#ef4444] border border-[#ef4444]/30 hover:bg-[#ef4444]/10 transition-colors cursor-pointer"
              @click="clearBgImage"
            >
              <Trash2 class="w-3.5 h-3.5" />
              删除
            </button>
          </div>
          <!-- 图片预览 -->
          <div v-if="bgImage" class="relative w-full h-24 rounded overflow-hidden border border-[#1e293b]">
            <img :src="bgImage" class="w-full h-full object-cover" />
            <div class="absolute inset-0 bg-black/20 pointer-events-none" />
          </div>
          <p class="text-xs text-[#8892a0]">
            支持 JPG、PNG、GIF 格式，最大 5MB
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
