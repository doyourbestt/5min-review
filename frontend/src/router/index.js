/**
 * 5分钟快速复盘 - 路由配置
 * ======================
 * AI维护注意点:
 * 1. 路由懒加载减少首屏加载时间
 * 2. meta.requiresAuth标记需要登录的页面
 * 3. 路由守卫处理权限校验
 */

import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@stores/user'

// AI维护注意点: 使用动态导入实现路由懒加载
const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@views/Home.vue'),
    meta: {
      title: '首页',
      requiresAuth: true
    }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@views/Login.vue'),
    meta: {
      title: '登录',
      requiresAuth: false,
      guestOnly: true // 仅未登录用户可访问
    }
  },
  {
    path: '/review',
    name: 'Review',
    component: () => import('@views/ReviewForm.vue'),
    meta: {
      title: '开始复盘',
      requiresAuth: true
    }
  },
  {
    path: '/checkin',
    name: 'CheckIn',
    component: () => import('@views/CheckIn.vue'),
    meta: {
      title: '打卡日历',
      requiresAuth: true
    }
  },
  {
    path: '/templates',
    name: 'Templates',
    component: () => import('@views/Templates.vue'),
    meta: {
      title: '模板管理',
      requiresAuth: true
    }
  },
  {
    path: '/stats',
    name: 'Stats',
    component: () => import('@views/Stats.vue'),
    meta: {
      title: '数据统计',
      requiresAuth: true
    }
  },
  // 可视化复盘模块
  {
    path: '/viz',
    name: 'Visualization',
    redirect: '/viz/board',
    meta: {
      title: '复盘可视化',
      requiresAuth: true
    }
  },
  {
    path: '/viz/paste',
    name: 'PasteReview',
    component: () => import('@views/PasteReview.vue'),
    meta: {
      title: '粘贴复盘',
      requiresAuth: true
    }
  },
  {
    path: '/viz/board',
    name: 'VisualizationBoard',
    component: () => import('@views/VisualizationBoard.vue'),
    meta: {
      title: '复盘看板',
      requiresAuth: true
    }
  },
  // 404页面
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@views/NotFound.vue'),
    meta: {
      title: '页面不存在'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  // AI维护注意点: 滚动行为配置
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// AI维护注意点: 全局前置守卫 - 权限校验
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  // 设置页面标题
  document.title = to.meta.title 
    ? `${to.meta.title} - 5分钟复盘` 
    : '5分钟快速复盘'
  
  // 需要登录但未登录
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next({
      path: '/login',
      query: { redirect: to.fullPath } // 保存原目标路径
    })
    return
  }
  
  // 仅游客可访问但已登录
  if (to.meta.guestOnly && userStore.isLoggedIn) {
    next({ path: '/' })
    return
  }
  
  next()
})

// AI维护注意点: 全局后置钩子 - 可用于页面统计
router.afterEach((to, from) => {
  // TODO: 接入页面访问统计
  // console.log(`Page view: ${to.path}`)
})

export default router
