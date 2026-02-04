<template>
  <div class="checkin-page">
    <div class="container">
      <!-- 页面头部 -->
      <header class="page-header">
        <button class="back-btn" @click="$router.back()">← 返回</button>
        <h1>打卡日历</h1>
      </header>

      <!-- 统计概览 -->
      <section class="stats-overview card">
        <div class="stat-item">
          <span class="value">{{ checkinData?.currentStreak || 0 }}</span>
          <span class="label">连续打卡(天)</span>
        </div>
        <div class="stat-item">
          <span class="value">{{ checkinData?.totalDays || 0 }}</span>
          <span class="label">累计打卡(天)</span>
        </div>
        <div class="stat-item">
          <span class="value">{{ todayHasReview ? '✓' : '○' }}</span>
          <span class="label">今日状态</span>
        </div>
      </section>

      <!-- 日历 -->
      <section class="calendar-section card">
        <div class="calendar-header">
          <button @click="prevMonth">‹</button>
          <h3>{{ currentYear }}年 {{ currentMonth }}月</h3>
          <button @click="nextMonth">›</button>
        </div>

        <div class="calendar-grid">
          <!-- 星期标题 -->
          <div class="weekday-header" v-for="day in weekdays" :key="day">
            {{ day }}
          </div>

          <!-- 日期格子 -->
          <div 
            v-for="date in calendarDays" 
            :key="date.date"
            class="calendar-day"
            :class="{
              'other-month': !date.isCurrentMonth,
              'today': date.isToday,
              'has-review': date.hasReview,
              'selected': selectedDate === date.date
            }"
            @click="selectDate(date)"
          >
            <span class="day-number">{{ date.day }}</span>
            <span v-if="date.reviewCount > 0" class="review-count">
              {{ date.reviewCount }}次
            </span>
          </div>
        </div>
      </section>

      <!-- 选中日期详情 -->
      <section class="date-detail card" v-if="selectedDate">
        <h3>{{ selectedDate }} 复盘记录</h3>
        <div v-if="selectedDateReviews.length > 0" class="review-list">
          <div 
            v-for="review in selectedDateReviews" 
            :key="review.id"
            class="review-item"
            @click="viewReview(review.id)"
          >
            <span class="title">{{ review.title }}</span>
            <span class="meta">{{ review.wordCount }}字 · {{ review.templateName }}</span>
          </div>
        </div>
        <p v-else class="no-data">该日期暂无复盘记录</p>
      </section>
    </div>
  </div>
</template>

<script setup>
/**
 * 5分钟快速复盘 - 打卡日历页
 * ==========================
 * AI维护注意点:
 * 1. 日历计算需考虑月份天数差异
 * 2. 热力图颜色深浅可表示复盘字数
 * 3. 跨月切换需重新加载数据
 */

import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { getCheckinStatus, getCalendarStats, getReviews } from '../api'

const router = useRouter()

// 响应式数据
const currentYear = ref(dayjs().year())
const currentMonth = ref(dayjs().month() + 1)
const checkinData = ref(null)
const calendarStats = ref({})
const selectedDate = ref(null)
const selectedDateReviews = ref([])
const todayHasReview = ref(false)

// 星期标题
const weekdays = ['日', '一', '二', '三', '四', '五', '六']

// 计算日历天数
const calendarDays = computed(() => {
  const year = currentYear.value
  const month = currentMonth.value
  
  // 当月第一天
  const firstDay = dayjs(`${year}-${month}-01`)
  // 当月最后一天
  const lastDay = firstDay.endOf('month')
  
  // 日历开始日期(周日)
  const startDate = firstDay.startOf('week')
  // 日历结束日期
  const endDate = lastDay.endOf('week')
  
  const days = []
  let current = startDate
  
  while (current.isBefore(endDate) || current.isSame(endDate, 'day')) {
    const dateStr = current.format('YYYY-MM-DD')
    const dayStats = calendarStats.value[dateStr] || {}
    
    days.push({
      date: dateStr,
      day: current.date(),
      isCurrentMonth: current.month() + 1 === month,
      isToday: current.isSame(dayjs(), 'day'),
      hasReview: dayStats.hasReview || false,
      reviewCount: dayStats.count || 0
    })
    
    current = current.add(1, 'day')
  }
  
  return days
})

// 切换月份
const prevMonth = () => {
  const newDate = dayjs(`${currentYear.value}-${currentMonth.value}-01`).subtract(1, 'month')
  currentYear.value = newDate.year()
  currentMonth.value = newDate.month() + 1
}

const nextMonth = () => {
  const newDate = dayjs(`${currentYear.value}-${currentMonth.value}-01`).add(1, 'month')
  currentYear.value = newDate.year()
  currentMonth.value = newDate.month() + 1
}

// 选择日期
const selectDate = async (date) => {
  selectedDate.value = date.date
  
  if (date.hasReview) {
    try {
      const res = await getReviews({
        startDate: date.date,
        endDate: date.date
      })
      selectedDateReviews.value = res.data?.reviews || []
    } catch (error) {
      console.error('获取复盘列表失败:', error)
    }
  } else {
    selectedDateReviews.value = []
  }
}

// 查看复盘详情
const viewReview = (reviewId) => {
  // AI维护注意点: 可跳转到复盘详情页或弹窗展示
  console.log('查看复盘:', reviewId)
}

// 加载日历数据
const loadCalendarData = async () => {
  try {
    const res = await getCalendarStats({
      year: currentYear.value,
      month: currentMonth.value
    })
    calendarStats.value = res.data?.dailyStats || {}
  } catch (error) {
    console.error('获取日历数据失败:', error)
  }
}

// 初始化数据
onMounted(async () => {
  try {
    // 并行加载数据
    const [checkinRes] = await Promise.all([
      getCheckinStatus(),
      loadCalendarData()
    ])
    
    checkinData.value = checkinRes.data
    todayHasReview.value = checkinRes.data?.checkinDates?.[dayjs().format('YYYY-MM-DD')]?.hasReview || false
  } catch (error) {
    console.error('加载数据失败:', error)
  }
})

// AI维护注意点: 切换月份时重新加载数据
watch([currentYear, currentMonth], loadCalendarData)
</script>

<style scoped>
.checkin-page {
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
  font-size: 14px;
}

.page-header h1 {
  font-size: 20px;
  margin: 0;
}

/* 统计概览 */
.stats-overview {
  display: flex;
  justify-content: space-around;
  margin-bottom: 30px;
  padding: 30px;
}

.stat-item {
  text-align: center;
}

.stat-item .value {
  display: block;
  font-size: 36px;
  font-weight: 700;
  color: var(--primary-color);
  margin-bottom: 8px;
}

.stat-item .label {
  color: var(--text-secondary);
  font-size: 14px;
}

/* 日历 */
.calendar-section {
  padding: 30px;
  margin-bottom: 30px;
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
}

.calendar-header button {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--text-secondary);
  padding: 5px 15px;
}

.calendar-header button:hover {
  color: var(--primary-color);
}

.calendar-header h3 {
  font-size: 18px;
  margin: 0;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
}

.weekday-header {
  text-align: center;
  padding: 10px;
  font-size: 14px;
  color: var(--text-tertiary);
  font-weight: 500;
}

.calendar-day {
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: all var(--transition-fast);
  background: var(--bg-color);
  position: relative;
}

.calendar-day:hover {
  background: #e8f4f8;
}

.calendar-day.other-month {
  color: var(--text-tertiary);
  background: transparent;
}

.calendar-day.today {
  border: 2px solid var(--primary-color);
  font-weight: 600;
}

.calendar-day.has-review {
  background: #d4edda;
}

.calendar-day.has-review::after {
  content: '';
  position: absolute;
  bottom: 4px;
  width: 4px;
  height: 4px;
  background: var(--success-color);
  border-radius: 50%;
}

.calendar-day.selected {
  background: var(--primary-color);
  color: white;
}

.day-number {
  font-size: 14px;
}

.review-count {
  font-size: 10px;
  color: var(--success-color);
  margin-top: 2px;
}

.calendar-day.selected .review-count {
  color: rgba(255, 255, 255, 0.8);
}

/* 日期详情 */
.date-detail {
  padding: 30px;
}

.date-detail h3 {
  margin-bottom: 20px;
  font-size: 18px;
}

.review-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.review-item {
  padding: 15px;
  background: var(--bg-color);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.review-item:hover {
  background: #e8f4f8;
}

.review-item .title {
  display: block;
  font-weight: 500;
  margin-bottom: 5px;
}

.review-item .meta {
  font-size: 12px;
  color: var(--text-tertiary);
}

.no-data {
  text-align: center;
  color: var(--text-tertiary);
  padding: 40px 0;
}
</style>
