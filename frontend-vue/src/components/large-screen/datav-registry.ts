/**
 * DataV Widget 注册表
 *
 * 集中管理 @kjgl77/datav-vue3 组件的按需导入
 * 不全局安装 DataV 插件，避免与自定义组件命名冲突
 */
import { defineAsyncComponent } from 'vue'

// ─── BorderBox 按需导入 ───────────────────────────────

export const BORDER_BOX_MAP: Record<string, ReturnType<typeof defineAsyncComponent>> = {
  'BorderBox1': defineAsyncComponent(() =>
    import('@kjgl77/datav-vue3').then(m => m.BorderBox1)
  ),
  'BorderBox2': defineAsyncComponent(() =>
    import('@kjgl77/datav-vue3').then(m => m.BorderBox2)
  ),
  'BorderBox3': defineAsyncComponent(() =>
    import('@kjgl77/datav-vue3').then(m => m.BorderBox3)
  ),
  'BorderBox4': defineAsyncComponent(() =>
    import('@kjgl77/datav-vue3').then(m => m.BorderBox4)
  ),
  'BorderBox5': defineAsyncComponent(() =>
    import('@kjgl77/datav-vue3').then(m => m.BorderBox5)
  ),
  'BorderBox6': defineAsyncComponent(() =>
    import('@kjgl77/datav-vue3').then(m => m.BorderBox6)
  ),
  'BorderBox7': defineAsyncComponent(() =>
    import('@kjgl77/datav-vue3').then(m => m.BorderBox7)
  ),
  'BorderBox8': defineAsyncComponent(() =>
    import('@kjgl77/datav-vue3').then(m => m.BorderBox8)
  ),
  'BorderBox9': defineAsyncComponent(() =>
    import('@kjgl77/datav-vue3').then(m => m.BorderBox9)
  ),
  'BorderBox10': defineAsyncComponent(() =>
    import('@kjgl77/datav-vue3').then(m => m.BorderBox10)
  ),
  'BorderBox11': defineAsyncComponent(() =>
    import('@kjgl77/datav-vue3').then(m => m.BorderBox11)
  ),
  'BorderBox12': defineAsyncComponent(() =>
    import('@kjgl77/datav-vue3').then(m => m.BorderBox12)
  ),
  'BorderBox13': defineAsyncComponent(() =>
    import('@kjgl77/datav-vue3').then(m => m.BorderBox13)
  ),
}

// ─── Decoration 按需导入 ───────────────────────────────

export const DECORATION_MAP: Record<string, ReturnType<typeof defineAsyncComponent>> = {
  'Decoration1': defineAsyncComponent(() =>
    import('@kjgl77/datav-vue3').then(m => m.Decoration1)
  ),
  'Decoration2': defineAsyncComponent(() =>
    import('@kjgl77/datav-vue3').then(m => m.Decoration2)
  ),
  'Decoration3': defineAsyncComponent(() =>
    import('@kjgl77/datav-vue3').then(m => m.Decoration3)
  ),
  'Decoration4': defineAsyncComponent(() =>
    import('@kjgl77/datav-vue3').then(m => m.Decoration4)
  ),
  'Decoration5': defineAsyncComponent(() =>
    import('@kjgl77/datav-vue3').then(m => m.Decoration5)
  ),
  'Decoration6': defineAsyncComponent(() =>
    import('@kjgl77/datav-vue3').then(m => m.Decoration6)
  ),
  'Decoration7': defineAsyncComponent(() =>
    import('@kjgl77/datav-vue3').then(m => m.Decoration7)
  ),
  'Decoration8': defineAsyncComponent(() =>
    import('@kjgl77/datav-vue3').then(m => m.Decoration8)
  ),
  'Decoration9': defineAsyncComponent(() =>
    import('@kjgl77/datav-vue3').then(m => m.Decoration9)
  ),
  'Decoration10': defineAsyncComponent(() =>
    import('@kjgl77/datav-vue3').then(m => m.Decoration10)
  ),
  'Decoration11': defineAsyncComponent(() =>
    import('@kjgl77/datav-vue3').then(m => m.Decoration11)
  ),
  'Decoration12': defineAsyncComponent(() =>
    import('@kjgl77/datav-vue3').then(m => m.Decoration12)
  ),
}

/**
 * 获取 BorderBox 组件
 * @param type 'BorderBox1' ~ 'BorderBox13'
 * @returns 异步组件或 undefined
 */
export function getBorderBox(type: string | null | undefined) {
  if (!type) return undefined
  return BORDER_BOX_MAP[type]
}

/**
 * 获取 Decoration 组件
 * @param type 'Decoration1' ~ 'Decoration12'
 * @returns 异步组件或 undefined
 */
export function getDecoration(type: string | null | undefined) {
  if (!type) return undefined
  return DECORATION_MAP[type]
}
