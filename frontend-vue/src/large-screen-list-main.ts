/**
 * 大屏模板列表页入口
 *
 * 独立页面，展示所有模板的卡片列表
 */
import { createApp } from 'vue'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import LargeScreenList from './components/large-screen/LargeScreenList.vue'
import './assets/main.css'

const app = createApp(LargeScreenList)
app.use(Antd)
app.mount('#app')
