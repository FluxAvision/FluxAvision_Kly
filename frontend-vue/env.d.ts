/// <reference types="vite/client" />

/** Vite define 注入的应用版本号（从项目根 VERSION 文件读取） */
declare const __APP_VERSION__: string

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}
