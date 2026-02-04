<template>
  <div class="viz-board">
    <!-- 顶部导航 -->
    <header class="board-header">
      <h1>🎯 {{ currentReview?.title || '每日复盘看板' }}</h1>
      <div class="header-actions">
        <!-- 日期选择器 -->
        <select v-model="selectedDate" @change="loadReview" class="date-select">
          <option v-for="day in availableDates" :key="day.date" :value="day.date">
            {{ day.date }} {{ day.title ? '- ' + day.title : '' }}
          </option>
        </select>
        
        <router-link to="/viz/paste" class="new-btn">
          + 新建复盘
        </router-link>
      </div>
    </header>

    <!-- 统计信息 -->
    <div class="stats-bar" v-if="currentReview">
      <div class="stat-item">
        <span class="number">{{ sharers.length }}</span>
        <span class="label">分享者</span>
      </div>
      <div class="stat-item">
        <span class="number">{{ totalInsights }}</span>
        <span class="label">干货条数</span>
      </div>
      <div class="stat-item">
        <span class="number">{{ totalLikes }}</span>
        <span class="label">总点赞</span>
      </div>
    </div>

    <!-- 人物卡片网格 -->
    <main class="cards-grid" v-if="sharers.length > 0">
      <PersonCard 
        v-for="sharer in sharers" 
        :key="sharer.name"
        :sharer="sharer"
        @avatar-updated="updateAvatar"
        @like-updated="updateLike"
      />
    </main>

    <!-- 空状态 -->
    <div v-else class="empty-board">
      <div class="empty-illustration">📊</div>
      <h2>暂无复盘数据</h2>
      <p>点击"新建复盘"开始记录每日干货</p>
      <router-link to="/viz/paste" class="cta-btn">
        开始记录
      </router-link>
    </div>

    <!-- 底部操作栏 -->
    <footer class="board-footer" v-if="sharers.length > 0">
      <div class="view-options">
        <button @click="scrollToTop" class="scroll-btn">
          ↑ 回到顶部
        </button>
      </div>
    </footer>
  </div>
</template>

<script setup>
/**
 * 复盘可视化 - 看板主页面
 * =======================
 * 核心功能：
 * 1. 展示所有分享者的人物卡片
 * 2. 日期切换查看历史复盘
 * 3. 统计数据展示
 * 4. 响应式网格布局（移动端单列，PC端多列）
 * 
 * AI维护注意点:
 * 1. 卡片网格使用CSS Grid，移动端单列、PC端2-3列
 * 2. 日期列表倒序排列，最新的在前
 * 3. URL参数支持直接访问特定日期
 * 4. 数据加载状态管理，避免闪烁
 */

import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'
import PersonCard from '../components/PersonCard.vue'

const route = useRoute()
const router = useRouter()

// 状态
const availableDates = ref([])
const selectedDate = ref('')
const currentReview = ref(null)
const sharers = ref([])
const loading = ref(false)

// 计算属性
const totalInsights = computed(() => {
  return sharers.value.reduce((sum, sharer) => sum + (sharer.insights?.length || 0), 0)
})

const totalLikes = computed(() => {
  return sharers.value.reduce((sum, sharer) => {
    return sum + sharer.insights?.reduce((s, i) => s + (i.likes || 0), 0) || 0
  }, 0)
})

/**
 * 获取可用日期列表
 */
const loadAvailableDates = async () => {
  try {
    const res = await api.get('/api/viz/dates')
    if (res.success) {
      availableDates.value = res.dates
      
      // 如果没有选中日期，默认选中最新的
      if (!selectedDate.value && res.dates.length > 0) {
        // 优先使用URL参数中的日期
        const urlDate = route.query.date
        if (urlDate && res.dates.find(d => d.date === urlDate)) {
          selectedDate.value = urlDate
        } else {
          selectedDate.value = res.dates[0].date
        }
        loadReview()
      }
    }
  } catch (err) {
    console.error('加载日期列表失败:', err)
  }
}

/**
 * 加载指定日期的复盘数据
 */
const loadReview = async () => {
  if (!selectedDate.value) return
  
  loading.value = true
  try {
    const res = await api.get(`/api/viz/reviews/${selectedDate.value}`)
    if (res.success) {
      currentReview.value = {
        date: res.date,
        title: res.title
      }
      sharers.value = res.sharers
      
      // 更新URL参数
      router.replace({ query: { date: selectedDate.value } })
    }
  } catch (err) {
    console.error('加载复盘失败:', err)
    if (err.response?.status === 404) {
      sharers.value = []
      currentReview.value = null
    }
  } finally {
    loading.value = false
  }
}

/**
 * 更新头像（被子组件调用）
 */
const updateAvatar = ({ name, url }) => {
  const sharer = sharers.value.find(s => s.name === name)
  if (sharer) {
    sharer.avatar_url = url
  }
}

/**
 * 更新点赞数（被子组件调用）
 */
const updateLike = ({ insightId, totalLikes }) => {
  // 更新本地数据
  for (const sharer of sharers.value) {
    const insight = sharer.insights?.find(i => i.id === insightId)
    if (insight) {
      insight.likes = totalLikes
      break
    }
  }
}

/**
 * 回到顶部
 */
const scrollToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// 监听URL参数变化
watch(() => route.query.date, (newDate) => {
  if (newDate && newDate !== selectedDate.value) {
    selectedDate.value = newDate
    loadReview()
  }
})

// 页面加载
onMounted(() => {
  loadAvailableDates()
})
</script>

<style scoped>
.viz-board {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 40px;
}

/* 头部 */
.board-header {
  background: white;
  padding: 20px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.board-header h1 {
  margin: 0;
  font-size: 22px;
  color: #333;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.date-select {
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  background: white;
  min-width: 200px;
}

.new-btn {
  padding: 10px 20px;
  background: var(--primary-color);
  color: white;
  text-decoration: none;
  border-radius: 6px;
  font-size: 14px;
  transition: opacity 0.2s;
}

.new-btn:hover {
  opacity: 0.9;
}

/* 统计栏 */
.stats-bar {
  display: flex;
  justify-content: center;
  gap: 40px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stat-item {
  text-align: center;
}

.number {
  display: block;
  font-size: 28px;
  font-weight: 700;
}

.label {
  font-size: 13px;
  opacity: 0.9;
}

/* 卡片网格 */
.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

/* 移动端单列 */
@media (max-width: 768px) {
  .cards-grid {
    grid-template-columns: 1fr;
    padding: 16px;
  }
  
  .board-header {
    flex-direction: column;
    text-align: center;
  }
  
  .header-actions {
    flex-direction: column;
    width: 100%;
  }
  
  .date-select {
    width: 100%;
  }
  
  .new-btn {
    width: 100%;
    text-align: center;
  }
  
  .stats-bar {
    gap: 20px;
    padding: 16px;
  }
  
  .number {
    font-size: 24px;
  }
}

/* 空状态 */
.empty-board {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
}

.empty-illustration {
  font-size: 80px;
  margin-bottom: 24px;
  opacity: 0.6;
}

.empty-board h2 {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 24px;
}

.empty-board p {
  color: #666;
  margin: 0 0 24px 0;
}

.cta-btn {
  padding: 14px 32px;
  background: var(--primary-color);
  color: white;
  text-decoration: none;
  border-radius: 25px;
  font-size: 16px;
  transition: transform 0.2s;
}

.cta-btn:hover {
  transform: scale(1.05);
}

/* 底部 */
.board-footer {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 90;
}

.scroll-btn {
  padding: 12px 20px;
  background: white;
  border: none;
  border-radius: 25px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.scroll-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.2);
}
</style>