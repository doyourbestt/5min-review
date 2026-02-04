<template>
  <div class="review-page">
    <div class="container">
      <!-- 页面头部 -->
      <header class="page-header">
        <button class="back-btn" @click="$router.back()">← 返回</button>
        <h1>开始复盘</h1>
        <div class="timer" v-if="showTimer">
          ⏱️ {{ formattedTime }}
        </div>
      </header>

      <!-- 模板选择 -->
      <section class="template-section" v-if="!selectedTemplate">
        <h2>选择复盘模板</h2>
        <div class="template-grid">
          <div 
            v-for="template in templates" 
            :key="template.id"
            class="template-card"
            @click="selectTemplate(template)"
          >
            <h3>{{ template.name }}</h3>
            <p>{{ template.description || '暂无描述' }}</p>
            <span class="type-badge">{{ templateTypeText(template.templateType) }}</span>
          </div>
        </div>
      </section>

      <!-- 复盘表单 -->
      <section class="review-form" v-else>
        <div class="form-header">
          <h2>{{ selectedTemplate.name }}</h2>
          <p class="date">{{ today }}</p>
        </div>

        <form @submit.prevent="submitReview">
          <!-- 复盘标题 -->
          <div class="form-group">
            <label>复盘标题</label>
            <input 
              v-model="reviewForm.title" 
              type="text" 
              placeholder="给你的复盘起个标题"
              class="title-input"
            >
          </div>

          <!-- 动态字段 -->
          <div 
            v-for="field in selectedTemplate.fields" 
            :key="field.id"
            class="form-group"
          >
            <label>
              {{ field.label }}
              <span v-if="field.required" class="required">*</span>
            </label>

            <!-- 文本输入 -->
            <input 
              v-if="field.fieldType === 'text'"
              v-model="reviewForm.answers[field.name]"
              type="text"
              :placeholder="field.placeholder"
              :required="field.required"
            >

            <!-- 多行文本 -->
            <textarea
              v-else-if="field.fieldType === 'textarea'"
              v-model="reviewForm.answers[field.name]"
              :placeholder="field.placeholder"
              :required="field.required"
              rows="4"
            ></textarea>

            <!-- 数字输入 -->
            <input 
              v-else-if="field.fieldType === 'number'"
              v-model.number="reviewForm.answers[field.name]"
              type="number"
              :placeholder="field.placeholder"
              :required="field.required"
            >

            <!-- 单选 -->
            <select
              v-else-if="field.fieldType === 'select'"
              v-model="reviewForm.answers[field.name]"
              :required="field.required"
            >
              <option value="">请选择</option>
              <option 
                v-for="option in field.config?.options || []" 
                :key="option.value"
                :value="option.value"
              >
                {{ option.label }}
              </option>
            </select>

            <!-- 多选 -->
            <div v-else-if="field.fieldType === 'multiselect'" class="checkbox-group">
              <label 
                v-for="option in field.config?.options || []" 
                :key="option.value"
                class="checkbox-label"
              >
                <input
                  type="checkbox"
                  :value="option.value"
                  v-model="multiSelectValues[field.name]"
                  @change="updateMultiSelect(field.name)"
                >
                {{ option.label }}
              </label>
            </div>

            <!-- 日期 -->
            <input 
              v-else-if="field.fieldType === 'date'"
              v-model="reviewForm.answers[field.name]"
              type="date"
              :required="field.required"
            >

            <!-- 评分 -->
            <div v-else-if="field.fieldType === 'rating'" class="rating-group">
              <span 
                v-for="star in 5" 
                :key="star"
                class="star"
                :class="{ active: star <= (reviewForm.answers[field.name] || 0) }"
                @click="reviewForm.answers[field.name] = star"
              >
                ★
              </span>
            </div>

            <!-- 复选框 -->
            <label v-else-if="field.fieldType === 'checkbox'" class="checkbox-single">
              <input
                type="checkbox"
                v-model="reviewForm.answers[field.name]"
                :true-value="true"
                :false-value="false"
              >
              {{ field.placeholder || '是/否' }}
            </label>
          </div>

          <!-- 操作按钮 -->
          <div class="form-actions">
            <button type="button" class="btn" @click="selectedTemplate = null">
              更换模板
            </button>
            <button 
              type="submit" 
              class="btn btn-primary"
              :disabled="isSubmitting"
            >
              {{ isSubmitting ? '保存中...' : '完成复盘' }}
            </button>
          </div>
        </form>
      </section>
    </div>
  </div>
</template>

<script setup>
/**
 * 5分钟快速复盘 - 复盘表单页
 * ==========================
 * AI维护注意点:
 * 1. 动态表单渲染需确保字段类型匹配
 * 2. 多选字段需特殊处理转换为数组
 * 3. 计时器功能需考虑页面隐藏时的处理
 * 4. 提交前校验必填字段
 */

import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { getTemplates, createReview } from './api'

const router = useRouter()

// 响应式数据
const templates = ref([])
const selectedTemplate = ref(null)
const isSubmitting = ref(false)
const showTimer = ref(true)
const elapsedSeconds = ref(0)
let timerInterval = null

// 多选字段临时存储
const multiSelectValues = reactive({})

// 复盘表单数据
const reviewForm = reactive({
  title: '',
  answers: {}
})

// 计算属性
const today = computed(() => dayjs().format('YYYY年MM月DD日'))

const formattedTime = computed(() => {
  const mins = Math.floor(elapsedSeconds.value / 60)
  const secs = elapsedSeconds.value % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
})

// 模板类型文本
const templateTypeText = (type) => {
  const map = {
    'daily': '每日复盘',
    'weekly': '每周复盘',
    'project': '项目复盘',
    'custom': '自定义'
  }
  return map[type] || type
}

// 选择模板
const selectTemplate = (template) => {
  selectedTemplate.value = template
  
  // 初始化表单数据
  reviewForm.title = `${dayjs().format('YYYY-MM-DD')} 复盘`
  reviewForm.answers = {}
  
  // 设置默认值
  template.fields.forEach(field => {
    if (field.defaultValue) {
      reviewForm.answers[field.name] = field.defaultValue
    }
    
    // 多选字段初始化
    if (field.fieldType === 'multiselect') {
      multiSelectValues[field.name] = []
    }
  })
  
  // 启动计时器
  startTimer()
}

// 更新多选值
const updateMultiSelect = (fieldName) => {
  reviewForm.answers[fieldName] = multiSelectValues[fieldName]
}

// 计时器
const startTimer = () => {
  elapsedSeconds.value = 0
  timerInterval = setInterval(() => {
    elapsedSeconds.value++
  }, 1000)
}

const stopTimer = () => {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
}

// 提交复盘
const submitReview = async () => {
  // AI维护注意点: 校验必填字段
  const requiredFields = selectedTemplate.value.fields.filter(f => f.required)
  for (const field of requiredFields) {
    const value = reviewForm.answers[field.name]
    if (!value || (Array.isArray(value) && value.length === 0)) {
      alert(`请填写必填项: ${field.label}`)
      return
    }
  }
  
  isSubmitting.value = true
  stopTimer()
  
  try {
    const data = {
      templateId: selectedTemplate.value.id,
      reviewDate: dayjs().format('YYYY-MM-DD'),
      title: reviewForm.title,
      answers: reviewForm.answers,
      durationMinutes: Math.ceil(elapsedSeconds.value / 60)
    }
    
    await createReview(data)
    
    // 提交成功，跳转到首页
    alert('复盘保存成功！')
    router.push('/')
    
  } catch (error) {
    console.error('提交复盘失败:', error)
    alert('保存失败，请重试')
    isSubmitting.value = false
  }
}

// AI维护注意点: 页面加载时获取模板列表
onMounted(async () => {
  try {
    const res = await getTemplates()
    templates.value = res.data?.templates || []
  } catch (error) {
    console.error('获取模板失败:', error)
  }
})

// AI维护注意点: 组件卸载时清理计时器
onUnmounted(() => {
  stopTimer()
})
</script>

<style scoped>
.review-page {
  min-height: 100vh;
  background: var(--bg-color);
  padding-bottom: 40px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
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

.back-btn:hover {
  color: var(--primary-color);
}

.page-header h1 {
  font-size: 20px;
  margin: 0;
}

.timer {
  font-family: monospace;
  font-size: 18px;
  color: var(--primary-color);
  font-weight: 600;
}

/* 模板选择 */
.template-section h2 {
  margin-bottom: 20px;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.template-card {
  background: var(--card-bg);
  border-radius: var(--border-radius);
  padding: 24px;
  cursor: pointer;
  transition: all var(--transition-fast);
  border: 2px solid transparent;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.template-card:hover {
  border-color: var(--primary-color);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.template-card h3 {
  font-size: 18px;
  margin-bottom: 10px;
}

.template-card p {
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 15px;
  min-height: 40px;
}

.type-badge {
  display: inline-block;
  padding: 4px 12px;
  background: var(--bg-color);
  border-radius: 20px;
  font-size: 12px;
  color: var(--text-tertiary);
}

/* 复盘表单 */
.review-form {
  background: var(--card-bg);
  border-radius: var(--border-radius);
  padding: 40px;
  max-width: 800px;
  margin: 0 auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.form-header {
  text-align: center;
  margin-bottom: 30px;
}

.form-header h2 {
  font-size: 24px;
  margin-bottom: 8px;
}

.form-header .date {
  color: var(--text-tertiary);
}

.form-group {
  margin-bottom: 25px;
}

.form-group label {
  display: block;
  margin-bottom: 10px;
  font-weight: 500;
}

.required {
  color: var(--error-color);
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 12px 15px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: 14px;
  font-family: inherit;
  transition: border-color var(--transition-fast);
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--primary-color);
}

.title-input {
  font-size: 18px !important;
  font-weight: 500;
}

/* 评分组件 */
.rating-group {
  display: flex;
  gap: 8px;
}

.star {
  font-size: 32px;
  color: #ddd;
  cursor: pointer;
  transition: color var(--transition-fast);
}

.star.active {
  color: #ffc107;
}

.star:hover {
  color: #ffc107;
}

/* 多选框 */
.checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.checkbox-single {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

/* 操作按钮 */
.form-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 40px;
  padding-top: 30px;
  border-top: 1px solid var(--border-color);
}

.form-actions .btn {
  padding: 12px 30px;
}
</style>
