/**
 * 应用版本号 — Vite define 会在构建时将 __APP_VERSION__ 替换为实际版本号字符串
 * 不要在 Vue template 中直接使用 __APP_VERSION__，需要通过此模块引用
 */
export const APP_VERSION: string = __APP_VERSION__
