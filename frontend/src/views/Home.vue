<template>
  <div class="home-page">
    <!-- 顶部导航栏 -->
    <header class="header">
      <div class="container header-content">
        <h1 class="logo">5分钟复盘</h1>
        <nav class="nav">
          <router-link to="/review" class="nav-link">开始复盘</router-link>
          <router-link to="/checkin" class="nav-link">打卡日历</router-link>
          <router-link to="/stats" class="nav-link">数据统计</router-link>
          <router-link to="/marks" class="nav-link">复盘标记</router-link>
          <div class="user-menu" @click="showUserMenu = !showUserMenu">
            <span>{{ userStore.userInfo?.username || '用户' }}</span>
            <div v-show="showUserMenu" class="dropdown">
              <button @click="handleLogout">退出登录</button>
            </div>
          </div>
        </nav>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="main">
      <div class="container">
        <!-- 欢迎区域 -->
        <section class="welcome-section">
          <h2>{{ greeting }}，{{ userStore.userInfo?.username || '朋友' }}！</h2>
          <p class="subtitle">
            {{ todayHasReview ? '今日已完成复盘，继续保持！' : '今天还没复盘哦，花5分钟记录一下吧' }}
          </p>
        </section>

        <!-- 快捷操作卡片 -->
        <section class="quick-actions">
          <div class="action-card" @click="$router.push('/review')">
            <div class="icon">📝</div>
            <h3>开始复盘</h3>
            <p>用5分钟回顾今天</p>
          </div>
          
          <div class="action-card" @click="$router.push('/checkin')">
            <div class="icon">📅</div>
            <h3>打卡日历</h3>
            <p>查看连续打卡记录</p>
          </div>
          
          <div class="action-card" @click="$router.push('/stats')">
            <div class="icon">📊</div>
            <h3>数据统计</h3>
            <p>复盘成果一目了然</p>
          </div>
        </section>

        <!-- 今日状态 -->
        <section class="today-status card">
          <h3>今日状态</h3>
          <div class="status-grid">
            <div class="status-item">
              <span class="label">今日复盘</span>
              <span :class="['value', todayHasReview ? 'success' : 'warning']">
                {{ todayHasReview ? '✓ 已完成' : '未打卡' }}
              </span>
            </div>
            <div class="status-item">
              <span class="label">连续打卡</span>
              <span class="value">{{ stats?.currentStreak || 0 }} 天</span>
            </div>
            <div class="status-item">
              <span class="label">总复盘次数</span>
              <span class="value">{{ stats?.totalReviews || 0 }} 次</span>
            </div>
            <div class="status-item">
              <span class="label">累计字数</span>
              <span class="value">{{ stats?.totalWords || 0 }} 字</span>
            </div>
          </div>
        </section>

        <!-- 最近复盘 -->
        <section class="recent-reviews card" v-if="recentReviews.length > 0">
          <h3>最近复盘</h3>
          <ul class="review-list">
            <li v-for="review in recentReviews" :key="review.id" class="review-item">
              <span class="date">{{ formatDate(review.reviewDate) }}</span>
              <span class="title">{{ review.title }}</span>
              <span class="words">{{ review.wordCount }} 字</span>
            </li>
          </ul>
        </section>
      </div>
    </main>
  </div>
</template>

<script setup>
/**
 * 5分钟快速复盘 - 首页
 * ==================
 * AI维护注意点:
 * 1. 首页加载时获取今日复盘状态和统计数据
 * 2. 用户菜单点击外部区域应关闭
 * 3. 数据加载状态需要loading处理
 */

import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { getOverview, getTodayReview, getRecentReviews } from '../api'
import dayjs from 'dayjs'

const router = useRouter()
const userStore = useUserStore()

// 响应式数据
const stats = ref(null)
const todayHasReview = ref(false)
const recentReviews = ref([])
const showUserMenu = ref(false)

// 计算属性
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 11) return '早上好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

// 格式化日期
const formatDate = (dateStr) => {
  return dayjs(dateStr).format('MM月DD日')
}

// 退出登录
const handleLogout = async () => {
  await userStore.logout()
  router.push('/login')
}

// AI维护注意点: 页面初始化数据加载
onMounted(async () => {
  try {
    // 并行加载多个接口
    const [overviewRes, todayRes, recentRes] = await Promise.all([
      getOverview(),
      getTodayReview(),
      getRecentReviews({ limit: 5 })
    ])
    
    stats.value = overviewRes.data
    todayHasReview.value = todayRes.data.hasReview
    recentReviews.value = recentRes.data?.reviews || []
  } catch (error) {
    console.error('加载首页数据失败:', error)
  }
})
</script>

<style scoped>
.home-page {
  min-height: 100vh;
}

/* 头部导航 */
.header {
  background: var(--card-bg);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: var(--header-height);
}

.logo {
  font-size: 20px;
  color: var(--primary-color);
  margin: 0;
}

.nav {
  display: flex;
  align-items: center;
  gap: 20px;
}

.nav-link {
  color: var(--text-secondary);
  text-decoration: none;
  transition: color var(--transition-fast);
}

.nav-link:hover,
.nav-link.router-link-active {
  color: var(--primary-color);
}

.user-menu {
  position: relative;
  cursor: pointer;
  padding: 8px 12px;
  background: var(--bg-color);
  border-radius: var(--border-radius);
}

.dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  background: var(--card-bg);
  border-radius: var(--border-radius);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 8px 0;
  min-width: 120px;
}

.dropdown button {
  width: 100%;
  padding: 8px 16px;
  border: none;
  background: none;
  cursor: pointer;
  text-align: left;
}

.dropdown button:hover {
  background: var(--bg-color);
}

/* 主内容区 */
.main {
  padding: 30px 0;
}

.welcome-section {
  margin-bottom: 30px;
}

.welcome-section h2 {
  font-size: 28px;
  margin-bottom: 8px;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 16px;
}

/* 快捷操作 */
.quick-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.action-card {
  background: var(--card-bg);
  border-radius: var(--border-radius);
  padding: 30px;
  text-align: center;
  cursor: pointer;
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.action-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.action-card h3 {
  font-size: 18px;
  margin-bottom: 8px;
}

.action-card p {
  color: var(--text-tertiary);
  font-size: 14px;
}

/* 今日状态 */
.today-status {
  margin-bottom: 30px;
}

.today-status h3 {
  margin-bottom: 20px;
  font-size: 18px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 20px;
}

.status-item {
  text-align: center;
  padding: 15px;
  background: var(--bg-color);
  border-radius: var(--border-radius);
}

.status-item .label {
  display: block;
  color: var(--text-tertiary);
  font-size: 14px;
  margin-bottom: 8px;
}

.status-item .value {
  display: block;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.status-item .value.success {
  color: var(--success-color);
}

.status-item .value.warning {
  color: var(--warning-color);
}

/* 最近复盘 */
.recent-reviews h3 {
  margin-bottom: 20px;
  font-size: 18px;
}

.review-list {
  list-style: none;
}

.review-item {
  display: flex;
  align-items: center;
  padding: 15px 0;
  border-bottom: 1px solid var(--border-color);
}

.review-item:last-child {
  border-bottom: none;
}

.review-item .date {
  color: var(--text-tertiary);
  font-size: 14px;
  width: 100px;
  flex-shrink: 0;
}

.review-item .title {
  flex: 1;
  font-weight: 500;
}

.review-item .words {
  color: var(--text-tertiary);
  font-size: 14px;
}
</style>
