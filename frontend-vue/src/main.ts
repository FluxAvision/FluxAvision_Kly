import { createApp } from 'vue'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import { Toaster } from 'vue-sonner'
import App from './App.vue'
import './assets/main.css'

const app = createApp(App)
app.use(Antd)
app.mount('#app')
