/**
 * 大屏展示页面入口
 * 独立的全屏展示页面，关闭时直接关闭窗口
 */
import { createApp } from 'vue'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import DataVVue3 from '@kjgl77/datav-vue3'
import LargeScreenApp from './LargeScreenApp.vue'
import './assets/main.css'

const app = createApp(LargeScreenApp)
app.use(Antd)
app.use(DataVVue3)
app.mount('#app')
