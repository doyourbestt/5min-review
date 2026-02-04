<template>
  <div class="stats-page">
    <div class="container">
      <header class="page-header">
        <button class="back-btn" @click="$router.push('/')">← 返回首页</button>
        <h1>数据统计</h1>
      </header>

      <!-- 概览卡片 -->
      <section class="overview-cards">
        <div class="stat-card card">
          <span class="value">{{ overview?.totalReviews || 0 }}</span>
          <span class="label">总复盘次数</span>
        </div>
        <div class="stat-card card">
          <span class="value">{{ overview?.totalWords || 0 }}</span>
          <span class="label">累计字数</span>
        </div>
        <div class="stat-card card">
          <span class="value">{{ overview?.currentStreak || 0 }}</span>
          <span class="label">连续打卡</span>
        </div>
        <div class="stat-card card">
          <span class="value">{{ overview?.monthReviews || 0 }}</span>
          <span class="label">本月复盘</span>
        </div>
      </section>

      <!-- 趋势图 -->
      <section class="trends-section card">
        <h3>复盘趋势（最近30天）</h3>
        <div class="trend-chart">
          <div 
            v-for="(day, index) in trends" 
            :key="index"
            class="trend-bar"
            :style="{ height: `${(day.count / maxCount) * 100}%` }"
            :title="`${day.date}: ${day.count}次`"
          ></div>
        </div>
      </section>

      <!-- 模板使用统计 -->
      <section class="templates-stats card" v-if="templateStats?.templates?.length">
        <h3>模板使用情况</h3>
        <div class="template-list">
          <div 
            v-for="t in templateStats.templates" 
            :key="t.templateId"
            class="template-stat-item"
          >
            <span class="name">{{ t.templateName }}</span>
            <div class="bar-container">
              <div 
                class="bar" 
                :style="{ width: `${t.percentage}%` }"
              ></div>
            </div>
            <span class="count">{{ t.count }}次 ({{ t.percentage }}%)</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getOverview, getTrends, getTemplateUsage } from '@api'

const overview = ref(null)
const trends = ref([])
const templateStats = ref(null)

const maxCount = computed(() => {
  const counts = trends.value.map(d => d.count)
  return Math.max(...counts, 1)
})

onMounted(async () => {
  try {
    const [overviewRes, trendsRes, templateRes] = await Promise.all([
      getOverview(),
      getTrends({ days: 30 }),
      getTemplateUsage()
    ])
    
    overview.value = overviewRes.data
    trends.value = trendsRes.data?.trends || []
    templateStats.value = templateRes.data
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
})
</script>

<style scoped>
.stats-page {
  min-height: 100vh;
  background: var(--bg-color);
  padding-bottom: 40px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px 0;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 30px;
}

.back-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
}

/* 概览卡片 */
.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  padding: 30px;
  text-align: center;
}

.stat-card .value {
  display: block;
  font-size: 36px;
  font-weight: 700;
  color: var(--primary-color);
  margin-bottom: 8px;
}

.stat-card .label {
  color: var(--text-secondary);
  font-size: 14px;
}

/* 趋势图 */
.trends-section {
  padding: 30px;
  margin-bottom: 30px;
}

.trends-section h3 {
  margin-bottom: 20px;
}

.trend-chart {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 150px;
  padding: 20px 0;
}

.trend-bar {
  flex: 1;
  background: var(--primary-color);
  border-radius: 2px 2px 0 0;
  min-height: 4px;
  opacity: 0.8;
  transition: opacity var(--transition-fast);
}

.trend-bar:hover {
  opacity: 1;
}

/* 模板统计 */
.templates-stats {
  padding: 30px;
}

.templates-stats h3 {
  margin-bottom: 20px;
}

.template-stat-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-color);
}

.template-stat-item:last-child {
  border-bottom: none;
}

.template-stat-item .name {
  width: 150px;
  flex-shrink: 0;
}

.bar-container {
  flex: 1;
  height: 8px;
  background: var(--bg-color);
  border-radius: 4px;
  overflow: hidden;
}

.bar {
  height: 100%;
  background: var(--primary-color);
  border-radius: 4px;
  transition: width var(--transition-normal);
}

.template-stat-item .count {
  width: 120px;
  text-align: right;
  font-size: 14px;
  color: var(--text-secondary);
}
</style>
