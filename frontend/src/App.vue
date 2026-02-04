<template>
  <div id="app" class="app-container">
    <!-- AI维护注意点: 使用keep-alive缓存特定页面 -->
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<script setup>
/**
 * 5分钟快速复盘 - 根组件
 * ======================
 * AI维护注意点:
 * 1. 全局状态监听(如登录状态变化)在此处理
 * 2. 全局初始化逻辑(如主题、语言)在此执行
 * 3. 性能优化: 避免在根组件放过多逻辑
 */

import { onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from './stores/user'

const router = useRouter()
const userStore = useUserStore()

// AI维护注意点: 应用初始化
onMounted(() => {
  // 尝试恢复登录状态
  userStore.initAuth()
  
  // 可在此添加全局初始化逻辑
  // 如：PWA注册、主题初始化等
})

// AI维护注意点: 监听登录状态变化，处理路由跳转
watch(() => userStore.isLoggedIn, (isLoggedIn) => {
  if (!isLoggedIn && router.currentRoute.value.meta.requiresAuth) {
    router.push('/login')
  }
})
</script>

<style>
/**
 * AI维护注意点:
 * 1. 全局CSS变量在此定义，确保主题一致性
 * 2. 移动端适配使用rem或viewport单位
 * 3. 动画过渡保持简洁，避免性能问题
 */

:root {
  /* 主题色 */
  --primary-color: #4a90e2;
  --primary-light: #6ba5e7;
  --primary-dark: #357abd;
  
  /* 功能色 */
  --success-color: #52c41a;
  --warning-color: #faad14;
  --error-color: #f5222d;
  --info-color: #1890ff;
  
  /* 中性色 */
  --text-primary: #262626;
  --text-secondary: #595959;
  --text-tertiary: #8c8c8c;
  --border-color: #d9d9d9;
  --bg-color: #f5f5f5;
  --card-bg: #ffffff;
  
  /* 尺寸 */
  --header-height: 60px;
  --max-content-width: 1200px;
  --border-radius: 8px;
  
  /* 动画 */
  --transition-fast: 0.15s ease;
  --transition-normal: 0.3s ease;
}

/* 重置样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 
               'Helvetica Neue', Arial, sans-serif;
  color: var(--text-primary);
  background-color: var(--bg-color);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 页面过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--transition-normal);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 应用容器 */
.app-container {
  min-height: 100vh;
}

/* 通用工具类 */
.container {
  max-width: var(--max-content-width);
  margin: 0 auto;
  padding: 0 20px;
}

.card {
  background: var(--card-bg);
  border-radius: var(--border-radius);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  padding: 20px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 20px;
  border: none;
  border-radius: var(--border-radius);
  cursor: pointer;
  font-size: 14px;
  transition: all var(--transition-fast);
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn-primary:hover {
  background: var(--primary-dark);
}

/* 响应式断点 */
@media (max-width: 768px) {
  :root {
    --header-height: 50px;
  }
  
  .container {
    padding: 0 15px;
  }
}
</style>
