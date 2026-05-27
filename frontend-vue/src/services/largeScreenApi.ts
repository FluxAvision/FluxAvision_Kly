/**
 * 大屏模板 API 服务
 *
 * 封装模板 CRUD 请求，统一处理响应格式
 */
import type { TemplateConfig } from '@/types/template-editor'

export interface ScreenTemplateItem {
  id: string
  name: string
  description: string
  thumbnail: string
  layout: string
  templateConfig: string | TemplateConfig
  canvasWidth: number
  canvasHeight: number
  backgroundColor: string
  backgroundImage: string
  isSystem: boolean
  isPublished: boolean
  createdAt: string
  updatedAt: string
}

/** API 统一响应格式 */
interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
}

/**
 * 获取模板列表
 */
export async function fetchTemplates(): Promise<ScreenTemplateItem[]> {
  const res = await fetch('/api/large-screen/templates')
  if (!res.ok) throw new Error(`获取模板列表失败: ${res.statusText}`)
  const json: ApiResponse<ScreenTemplateItem[]> = await res.json()
  if (!json.success) throw new Error(json.message || '获取模板列表失败')
  return json.data || []
}

/**
 * 获取单个模板详情
 */
export async function fetchTemplateDetail(id: string): Promise<ScreenTemplateItem | null> {
  const res = await fetch(`/api/large-screen/templates/${id}`)
  if (!res.ok) {
    if (res.status === 404) return null
    throw new Error(`获取模板详情失败: ${res.statusText}`)
  }
  const json: ApiResponse<ScreenTemplateItem> = await res.json()
  if (!json.success) throw new Error(json.message || '获取模板详情失败')
  return json.data || null
}

/**
 * 创建新模板
 */
export async function createTemplate(data: {
  name?: string
  description?: string
  templateConfig?: TemplateConfig
  canvasWidth?: number
  canvasHeight?: number
  backgroundColor?: string
}): Promise<ScreenTemplateItem> {
  const body: Record<string, any> = {}

  if (data.name) body.name = data.name
  if (data.description) body.description = data.description
  if (data.templateConfig) body.templateConfig = data.templateConfig
  if (data.canvasWidth) body.canvasWidth = data.canvasWidth
  if (data.canvasHeight) body.canvasHeight = data.canvasHeight
  if (data.backgroundColor) body.backgroundColor = data.backgroundColor

  const res = await fetch('/api/large-screen/templates', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const errJson = await res.json().catch(() => ({}))
    throw new Error(errJson.message || `创建模板失败: ${res.statusText}`)
  }
  const json: ApiResponse<ScreenTemplateItem> = await res.json()
  if (!json.success) throw new Error(json.message || '创建模板失败')
  return json.data!
}

/**
 * 更新模板
 */
export async function updateTemplate(
  id: string,
  data: {
    name?: string
    description?: string
    templateConfig?: TemplateConfig
    canvasWidth?: number
    canvasHeight?: number
    backgroundColor?: string
  }
): Promise<ScreenTemplateItem> {
  const body: Record<string, any> = {}

  if (data.name !== undefined) body.name = data.name
  if (data.description !== undefined) body.description = data.description
  if (data.templateConfig !== undefined) body.templateConfig = data.templateConfig
  if (data.canvasWidth !== undefined) body.canvasWidth = data.canvasWidth
  if (data.canvasHeight !== undefined) body.canvasHeight = data.canvasHeight
  if (data.backgroundColor !== undefined) body.backgroundColor = data.backgroundColor

  const res = await fetch(`/api/large-screen/templates/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const errJson = await res.json().catch(() => ({}))
    throw new Error(errJson.message || `更新模板失败: ${res.statusText}`)
  }
  const json: ApiResponse<ScreenTemplateItem> = await res.json()
  if (!json.success) throw new Error(json.message || '更新模板失败')
  return json.data!
}

/**
 * 删除模板
 */
export async function deleteTemplate(id: string): Promise<void> {
  const res = await fetch(`/api/large-screen/templates/${id}`, {
    method: 'DELETE',
  })
  if (!res.ok) {
    const errJson = await res.json().catch(() => ({}))
    throw new Error(errJson.message || `删除模板失败: ${res.statusText}`)
  }
  const json: ApiResponse = await res.json()
  if (!json.success) throw new Error(json.message || '删除模板失败')
}
