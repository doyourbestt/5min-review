<template>
  <div class="login-page">
    <div class="login-container">
      <!-- 左侧品牌区 -->
      <div class="brand-section">
        <h1 class="brand-title">5分钟复盘</h1>
        <p class="brand-desc">
          每天5分钟，<br>
          让成长看得见
        </p>
        <ul class="feature-list">
          <li>✓ 快速记录，不占用太多时间</li>
          <li>✓ 多种模板，适应不同场景</li>
          <li>✓ 数据统计，追踪成长轨迹</li>
          <li>✓ 打卡激励，养成复盘习惯</li>
        </ul>
      </div>

      <!-- 右侧表单区 -->
      <div class="form-section">
        <div class="form-card">
          <h2>欢迎加入</h2>
          <p class="subtitle">输入群昵称即可开始复盘</p>
          
          <form @submit.prevent="handleSubmit">
            <div class="form-group">
              <label>群昵称</label>
              <input 
                v-model="nickname" 
                type="text" 
                placeholder="请输入群昵称"
                :class="{ error: error }"
                @blur="validate"
                @keyup.enter="handleSubmit"
              >
              <span v-if="error" class="error-msg">{{ error }}</span>
            </div>

            <div v-if="submitError" class="submit-error">
              {{ submitError }}
            </div>

            <button 
              type="submit" 
              class="btn btn-primary submit-btn"
              :disabled="isSubmitting || !nickname"
            >
              {{ isSubmitting ? '进入中...' : '进入复盘' }}
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const nickname = ref('')
const error = ref('')
const isSubmitting = ref(false)
const submitError = ref('')

const validate = () => {
  error.value = ''
  if (!nickname.value) {
    error.value = '请输入群昵称'
    return false
  } else if (nickname.value.length < 2 || nickname.value.length > 20) {
    error.value = '昵称长度为2-20个字符'
    return false
  }
  return true
}

const handleSubmit = async () => {
  submitError.value = ''
  
  if (!validate()) {
    return
  }
  
  isSubmitting.value = true
  
  try {
    await userStore.login({
      username: nickname.value
    })
    
    // 登录成功后跳转
    const redirect = route.query.redirect || '/'
    router.push(redirect)
    
  } catch (err) {
    submitError.value = err.message || '进入失败，请重试'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-container {
  display: flex;
  width: 100%;
  max-width: 1000px;
  background: var(--card-bg);
  border-radius: var(--border-radius);
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

/* 品牌区域 */
.brand-section {
  flex: 1;
  padding: 60px;
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
  color: white;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.brand-title {
  font-size: 36px;
  margin-bottom: 20px;
  font-weight: 700;
}

.brand-desc {
  font-size: 24px;
  line-height: 1.6;
  margin-bottom: 40px;
  opacity: 0.9;
}

.feature-list {
  list-style: none;
}

.feature-list li {
  margin-bottom: 15px;
  font-size: 16px;
  opacity: 0.85;
}

/* 表单区域 */
.form-section {
  flex: 1;
  padding: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.form-card {
  width: 100%;
  max-width: 360px;
}

.form-card h2 {
  font-size: 28px;
  margin-bottom: 10px;
  text-align: center;
}

.subtitle {
  text-align: center;
  color: var(--text-secondary);
  margin-bottom: 30px;
  font-size: 14px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--text-secondary);
}

.form-group input {
  width: 100%;
  padding: 12px 15px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: 14px;
  transition: border-color var(--transition-fast);
}

.form-group input:focus {
  outline: none;
  border-color: var(--primary-color);
}

.form-group input.error {
  border-color: var(--error-color);
}

.error-msg {
  display: block;
  color: var(--error-color);
  font-size: 12px;
  margin-top: 5px;
}

.submit-error {
  background: #fff2f0;
  border: 1px solid #ffccc7;
  color: var(--error-color);
  padding: 12px;
  border-radius: var(--border-radius);
  margin-bottom: 20px;
  font-size: 14px;
}

.submit-btn {
  width: 100%;
  padding: 14px;
  font-size: 16px;
  margin-top: 10px;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 响应式 */
@media (max-width: 768px) {
  .login-container {
    flex-direction: column;
  }
  
  .brand-section {
    padding: 40px 30px;
    text-align: center;
  }
  
  .brand-title {
    font-size: 28px;
  }
  
  .brand-desc {
    font-size: 18px;
    margin-bottom: 20px;
  }
  
  .form-section {
    padding: 40px 30px;
  }
}
</style>
