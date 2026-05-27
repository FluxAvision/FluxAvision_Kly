/**
 * useThemeResolver
 *
 * 主题继承机制：模板级 ThemeConfig + 组件级 ComponentStyles → 合并后的组件样式
 * 合并规则：组件显式设置的字段覆盖模板，未设置的从模板继承
 */
import { computed, type ComputedRef } from 'vue'
import type { ThemeConfig, ComponentConfig, ComponentStyles } from '@/types/template-editor'

/**
 * 解析组件最终样式
 * @param theme 模板级主题配置（可选）
 * @param component 组件配置
 * @returns 合并后的组件样式
 */
export function resolveComponentStyle(
  theme: ThemeConfig | undefined | null,
  component: ComponentConfig
): ComponentStyles {
  const s = component.styles ?? {}
  if (!theme) return s

  // 构建继承结果：以 theme 为基底，组件显式设置的覆盖
  const resolved: ComponentStyles = {
    // 从 Theme 继承默认值
    color: theme.textColor,
    fontSize: theme.fontSize,
    fontFamily: theme.fontFamily,
    backgroundColor: theme.backgroundColor,
    borderColor: theme.borderColor,
    opacity: theme.opacity,
  }

  // 组件显式设置的字段覆盖模板
  return {
    ...resolved,
    ...stripUndefined(s),
  }
}

/**
 * 移除对象中值为 undefined 的字段
 * 用于判断组件是否显式设置了某个样式字段
 */
function stripUndefined<T extends Record<string, any>>(obj: T): Partial<T> {
  const result: Partial<T> = {}
  for (const key of Object.keys(obj) as Array<keyof T>) {
    if (obj[key] !== undefined) {
      result[key] = obj[key]
    }
  }
  return result
}

/**
 * 从主题解析 CSS 变量
 * 返回可注入到容器元素上的 style 对象
 */
export function resolveThemeCSSVars(
  theme: ThemeConfig | undefined | null
): Record<string, string> {
  if (!theme) return {}

  const vars: Record<string, string> = {}

  if (theme.primaryColor) vars['--theme-primary'] = theme.primaryColor
  if (theme.secondaryColor) vars['--theme-secondary'] = theme.secondaryColor
  if (theme.backgroundColor) vars['--theme-bg'] = theme.backgroundColor
  if (theme.textColor) vars['--theme-text'] = theme.textColor
  if (theme.titleColor) vars['--theme-title'] = theme.titleColor
  if (theme.borderColor) vars['--theme-border'] = theme.borderColor
  if (theme.fontFamily) vars['--theme-font-family'] = theme.fontFamily

  // 自定义 CSS 变量
  if (theme.cssVars) {
    Object.assign(vars, theme.cssVars)
  }

  return vars
}

/**
 * 主题响应式 composable
 * 输入：模板级 ThemeConfig + 组件列表
 * 输出：每个组件合并后的样式 Map
 */
export function useThemeResolver(
  theme: ComputedRef<ThemeConfig | undefined | null> | ThemeConfig | undefined | null,
  components: ComponentConfig[]
): ComputedRef<Map<string, ComponentStyles>> {
  const themeValue = computed(() => {
    if (!theme) return undefined
    if (typeof theme === 'function' || (theme as any).value !== undefined) {
      return (theme as ComputedRef<ThemeConfig | undefined | null>).value
    }
    return theme as ThemeConfig | undefined | null
  })

  return computed(() => {
    const t = themeValue.value
    const result = new Map<string, ComponentStyles>()

    for (const comp of components) {
      result.set(comp.id, resolveComponentStyle(t, comp))
    }

    return result
  })
}
