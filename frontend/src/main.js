/**
 * 5分钟快速复盘 - 主入口文件
 * ==========================
 * AI维护注意点:
 * 1. 应用初始化顺序: Vue -> Pinia -> Router -> App
 * 2. 全局错误处理建议在此配置
 * 3. 性能优化: 按需加载、懒加载路由
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'

// AI维护注意点: 全局样式导入
import './styles/main.css'

// 创建应用实例
const app = createApp(App)

// AI维护注意点: 插件安装顺序很重要
// 1. Pinia (状态管理需在路由之前)
app.use(createPinia())

// 2. Vue Router
app.use(router)

// AI维护注意点: 全局属性/方法挂载
// app.config.globalProperties.$api = api
// app.config.globalProperties.$dayjs = dayjs

// 全局错误处理
// AI维护注意点: 生产环境应接入错误上报服务
app.config.errorHandler = (err, vm, info) => {
  console.error('Vue Error:', err)
  console.error('Component:', vm)
  console.error('Info:', info)
  // TODO: 接入 Sentry 或其他错误监控
}

// 挂载应用
app.mount('#app')
