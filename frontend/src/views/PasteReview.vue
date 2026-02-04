<template>
  <div class="paste-page">
    <!-- 顶部导航 -->
    <header class="header">
      <h1>📋 复盘可视化</h1>
      <router-link to="/viz/board" class="view-btn">
        查看看板 →
      </router-link>
    </header>

    <!-- 主内容区 -->
    <main class="main">
      <!-- 左侧：Markdown输入 -->
      <section class="input-section">
        <div class="date-selector">
          <label>复盘日期</label>
          <input type="date" v-model="reviewDate" />
        </div>

        <div class="editor-wrapper">
          <textarea
            v-model="markdownContent"
            class="markdown-editor"
            placeholder="在此粘贴每日复盘干货Markdown...

示例格式：
## 李阳州 🕰️
- 时间价值化魔法：把每小时明码标价
- 招聘反思：坦诚但要摸清核心需求

## 小马哥 🔥
- 行业洞察：知识付费时代逐渐退潮"
            @input="autoParse"
          ></textarea>
          
          <div class="toolbar">
            <button @click="manualParse" :disabled="!markdownContent" class="parse-btn">
              {{ parsing ? '解析中...' : '👁️ 预览效果' }}
            </button>
            <button @click="saveReview" :disabled="!parsedData.length" class="save-btn">
              {{ saving ? '保存中...' : '💾 保存到看板' }}
            </button>
          </div>
        </div>

        <!-- 快捷提示 -->
        <div class="tips">
          <h4>💡 格式提示</h4>
          <ul>
            <li>使用 <code>## 姓名 表情</code> 标记分享者</li>
            <li>使用 <code>- 主题：内容</code> 记录干货</li>
            <li>支持从微信/飞书直接复制粘贴</li>
          </ul>
        </div>
      </section>

      <!-- 右侧：预览区 -->
      <section class="preview-section" v-if="parsedData.length > 0">
        <h3>📊 预览（{{ parsedData.length }}位分享者）</h3>
        
        <div class="preview-cards">
          <div 
            v-for="sharer in parsedData" 
            :key="sharer.name"
            class="preview-card"
          >
            <div class="card-header">
              <img :src="getAvatarUrl(sharer.name)" class="avatar" />
              <span class="name">{{ sharer.name }}</span>
              <span class="emoji">{{ sharer.emoji }}</span>
            </div>
            
            <div class="insights-preview">
              <div 
                v-for="(insight, idx) in sharer.insights" 
                :key="idx"
                class="insight-item"
              >
                <span class="topic">{{ insight.topic }}</span>
                <span class="preview-text">{{ insight.content.substring(0, 50) }}...</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 分享者头像管理 -->
        <div class="avatar-manager">
          <h4>🎨 上传头像（可选）</h4>
          <div class="avatar-list">
            <div 
              v-for="sharer in parsedData" 
              :key="sharer.name"
              class="avatar-uploader"
            >
              <img :src="getAvatarUrl(sharer.name)" class="preview-avatar" />
              <span class="sharer-name">{{ sharer.name }}</span>
              <input 
                type="file" 
                accept="image/*"
                @change="uploadAvatar($event, sharer.name)"
                class="file-input"
              />
            </div>
          </div>
        </div>
      </section>

      <!-- 空状态 -->
      <section class="empty-state" v-else>
        <div class="empty-icon">📝</div>
        <p>在左侧粘贴Markdown复盘文本<br>即可生成可视化人物卡片</p>
      </section>
    </main>

    <!-- 成功提示 -->
    <div v-if="showSuccess" class="success-toast">
      ✅ 保存成功！正在跳转到看板...
    </div>
  </div>
</template>

<script setup>
/**
 * 复盘可视化 - Markdown粘贴页
 * =============================
 * 核心功能：
 * 1. Markdown文本粘贴与实时预览
 * 2. 自动解析分享者和干货
 * 3. 头像上传管理
 * 4. 保存到数据库
 * 
 * AI维护注意点:
 * 1. 防抖处理解析请求，避免频繁API调用
 * 2. 本地缓存未保存的内容，防止意外丢失
 * 3. 头像预览使用默认头像，上传后实时更新
 */

import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()

// 状态
const markdownContent = ref('')
const reviewDate = ref(new Date().toISOString().split('T')[0])
const parsedData = ref([])
const parsing = ref(false)
const saving = ref(false)
const showSuccess = ref(false)
const uploadedAvatars = ref({}) // 记录已上传的头像

// 防抖定时器
let parseTimer = null

/**
 * 自动生成设备指纹
 * AI维护注意点：用于点赞防重复，不需要登录
 */
const getDeviceId = () => {
  let deviceId = localStorage.getItem('viz_device_id')
  if (!deviceId) {
    deviceId = 'viz_' + Math.random().toString(36).substr(2, 9)
    localStorage.setItem('viz_device_id', deviceId)
  }
  return deviceId
}

/**
 * 获取头像URL
 * AI维护注意点：优先使用已上传的头像，其次是默认头像
 */
const getAvatarUrl = (name) => {
  if (uploadedAvatars.value[name]) {
    return uploadedAvatars.value[name]
  }
  return `http://localhost:5000/static/avatars/default/${name[0]}.png`
}

/**
 * 自动解析（防抖）
 */
const autoParse = () => {
  if (parseTimer) {
    clearTimeout(parseTimer)
  }
  parseTimer = setTimeout(() => {
    if (markdownContent.value.trim().length > 20) {
      manualParse()
    }
  }, 800)
}

/**
 * 手动解析Markdown
 */
const manualParse = async () => {
  if (!markdownContent.value.trim()) return
  
  parsing.value = true
  try {
    const res = await api.post('/api/viz/parse', {
      markdown: markdownContent.value,
      review_date: reviewDate.value
    })
    
    if (res.success) {
      parsedData.value = res.sharers
    }
  } catch (err) {
    console.error('解析失败:', err)
    alert('解析失败：' + (err.message || '请检查格式'))
  } finally {
    parsing.value = false
  }
}

/**
 * 上传头像
 */
const uploadAvatar = async (event, sharerName) => {
  const file = event.target.files[0]
  if (!file) return
  
  // 文件校验
  if (!file.type.startsWith('image/')) {
    alert('请选择图片文件')
    return
  }
  
  if (file.size > 5 * 1024 * 1024) {
    alert('图片不能超过5MB')
    return
  }
  
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const res = await api.post(`/api/viz/upload-avatar/${sharerName}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (res.success) {
      uploadedAvatars.value[sharerName] = 'http://localhost:5000' + res.avatar_url
      alert(`${sharerName}的头像上传成功！`)
    }
  } catch (err) {
    console.error('上传失败:', err)
    alert('上传失败：' + (err.message || '请重试'))
  }
}

/**
 * 保存复盘到数据库
 */
const saveReview = async () => {
  if (!parsedData.value.length) return
  
  saving.value = true
  try {
    const res = await api.post('/api/viz/save', {
      markdown: markdownContent.value,
      review_date: reviewDate.value,
      device_id: getDeviceId()
    })
    
    if (res.success) {
      showSuccess.value = true
      
      // 清空缓存
      localStorage.removeItem('viz_draft')
      
      // 2秒后跳转到看板
      setTimeout(() => {
        router.push(`/viz/board?date=${reviewDate.value}`)
      }, 2000)
    }
  } catch (err) {
    console.error('保存失败:', err)
    alert('保存失败：' + (err.message || '请重试'))
  } finally {
    saving.value = false
  }
}

/**
 * 本地缓存恢复
 * AI维护注意点：防止用户意外刷新丢失未保存内容
 */
const saveDraft = () => {
  if (markdownContent.value) {
    localStorage.setItem('viz_draft', JSON.stringify({
      content: markdownContent.value,
      date: reviewDate.value,
      timestamp: Date.now()
    }))
  }
}

const restoreDraft = () => {
  const draft = localStorage.getItem('viz_draft')
  if (draft) {
    const data = JSON.parse(draft)
    // 只恢复24小时内的草稿
    if (Date.now() - data.timestamp < 24 * 60 * 60 * 1000) {
      markdownContent.value = data.content
      reviewDate.value = data.date
      manualParse()
    }
  }
}

// 监听内容变化自动保存草稿
watch(markdownContent, saveDraft)
watch(reviewDate, saveDraft)

// 页面加载时恢复草稿
onMounted(() => {
  restoreDraft()
})
</script>

<style scoped>
.paste-page {
  min-height: 100vh;
  background: #f5f5f5;
}

/* 头部 */
.header {
  background: white;
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header h1 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.view-btn {
  padding: 8px 16px;
  background: var(--primary-color);
  color: white;
  text-decoration: none;
  border-radius: 20px;
  font-size: 14px;
  transition: opacity 0.2s;
}

.view-btn:hover {
  opacity: 0.9;
}

/* 主内容区 */
.main {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .main {
    grid-template-columns: 1fr;
  }
}

/* 输入区 */
.input-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.date-selector {
  background: white;
  padding: 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.date-selector label {
  font-weight: 500;
  color: #666;
}

.date-selector input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.editor-wrapper {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.markdown-editor {
  width: 100%;
  min-height: 400px;
  padding: 20px;
  border: none;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 14px;
  line-height: 1.8;
  resize: vertical;
  outline: none;
}

.toolbar {
  padding: 12px 20px;
  background: #fafafa;
  border-top: 1px solid #eee;
  display: flex;
  gap: 12px;
}

.toolbar button {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.parse-btn {
  background: #e3f2fd;
  color: #1976d2;
}

.save-btn {
  background: var(--primary-color);
  color: white;
}

.toolbar button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 提示区 */
.tips {
  background: #fff8e1;
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid #ffc107;
}

.tips h4 {
  margin: 0 0 12px 0;
  color: #f57c00;
}

.tips ul {
  margin: 0;
  padding-left: 20px;
  color: #666;
  font-size: 13px;
}

.tips li {
  margin: 6px 0;
}

.tips code {
  background: rgba(0,0,0,0.05);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: monospace;
}

/* 预览区 */
.preview-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.preview-section h3 {
  margin: 0;
  color: #333;
}

.preview-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.preview-card {
  background: white;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

.name {
  font-weight: 600;
  color: #333;
}

.emoji {
  font-size: 18px;
}

.insights-preview {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.insight-item {
  padding: 8px 12px;
  background: #f5f5f5;
  border-radius: 4px;
  font-size: 13px;
}

.topic {
  font-weight: 500;
  color: var(--primary-color);
  display: block;
  margin-bottom: 4px;
}

.preview-text {
  color: #666;
  display: block;
}

/* 头像管理 */
.avatar-manager {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.avatar-manager h4 {
  margin: 0 0 16px 0;
  color: #333;
}

.avatar-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.avatar-uploader {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.preview-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  object-fit: cover;
  cursor: pointer;
  transition: transform 0.2s;
}

.preview-avatar:hover {
  transform: scale(1.05);
}

.sharer-name {
  font-size: 12px;
  color: #666;
}

.file-input {
  position: absolute;
  width: 60px;
  height: 60px;
  opacity: 0;
  cursor: pointer;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  color: #999;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state p {
  line-height: 1.8;
}

/* 成功提示 */
.success-toast {
  position: fixed;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  background: #4caf50;
  color: white;
  padding: 12px 24px;
  border-radius: 25px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  animation: slideDown 0.3s ease;
  z-index: 1000;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}
</style>
