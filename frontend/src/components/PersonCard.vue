<template>
  <div 
    class="person-card" 
    :class="{ 
      'click-active': clickActive, 
      'long-press-active': longPressActive 
    }"
    @click="handleClick"
    @touchstart="touchStart"
    @touchend="touchEnd"
    @touchcancel="touchCancel"
    @contextmenu.prevent="handleLongPress"
  >
    <!-- 卡片头部：头像+姓名+表情 -->
    <header class="card-header">
      <div class="avatar-wrapper" @click.stop="triggerAvatarUpload">
        <img :src="avatarUrl" class="avatar" :alt="sharer.name" loading="lazy" />
        <div class="avatar-overlay" v-if="!hasCustomAvatar">
          <span>上传</span>
        </div>
        <input 
          type="file" 
          accept="image/*" 
          class="avatar-input" 
          @change="handleAvatarUpload"
          :title="hasCustomAvatar ? '更换头像' : '上传头像'"
        />
      </div>
      <div class="sharer-info">
        <h3 class="name">{{ sharer.name }}</h3>
        <span class="emoji" v-if="sharer.emoji">{{ sharer.emoji }}</span>
      </div>
      <!-- 长按提示 -->
      <div class="long-press-hint" v-if="longPressActive">
        长按查看详情
      </div>
    </header>

    <!-- 干货列表 -->
    <div class="insights-list">
      <div v-for="insight in sharer.insights" :key="insight.id" class="insight-item"
        :class="{ 'liked': isLiked(insight.id) }" @click="toggleLike(insight)">
        <div class="insight-header">
          <span class="topic">{{ insight.topic }}</span>
          <div class="like-wrapper">
            <button class="like-btn" :class="{ 'active': isLiked(insight.id) }" @click.stop="toggleLike(insight)">
              <span class="heart">{{ isLiked(insight.id) ? '❤️' : '🤍' }}</span>
              <span class="count">{{ insight.likes || 0 }}</span>
            </button>
          </div>
        </div>
        <p class="content">{{ insight.content }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 人物卡片组件
 * =============
 * 核心功能：
 * 1. 展示分享者头像、姓名、表情
 * 2. 展示多条干货内容
 * 3. 每条干货独立点赞
 * 4. 移动端touch动效/PC端hover动效
 * 
 * AI维护注意点:
 * 1. 图片懒加载优化性能
 * 2. 本地存储已点赞的insight_id，快速判断状态
 * 3. touch事件与click事件防冲突
 * 4. 头像上传失败时优雅降级
 */

import { ref, computed } from 'vue'
import api from '../api'

const props = defineProps({
  sharer: {
    type: Object,
    required: true,
    // { name, emoji, avatar_url, insights: [{ id, topic, content, likes }] }
  }
})

const emit = defineEmits(['avatar-updated', 'like-updated'])

// 状态
const touchActive = ref(false)
const clickActive = ref(false)
const longPressActive = ref(false)
const likedInsights = ref(new Set())

// 长按定时器
let longPressTimer = null
let clickTimer = null

const hasCustomAvatar = computed(() => {
  return props.sharer.avatar_url && !props.sharer.avatar_url.includes('/default/')
})

/**
 * 获取头像URL
 * AI维护注意点：处理相对路径转绝对路径
 */
const avatarUrl = computed(() => {
  const url = props.sharer.avatar_url
  if (!url) {
    return `http://localhost:5000/static/avatars/default/${props.sharer.name[0]}.png`
  }
  if (url.startsWith('http')) {
    return url
  }
  return `http://localhost:5000${url}`
})

/**
 * 获取设备指纹
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
 * 检查是否已点赞
 */
const isLiked = (insightId) => {
  return likedInsights.value.has(insightId)
}

/**
 * 切换点赞状态
 * AI维护注意点：防止重复点击，使用防抖
 */
let likingSet = new Set()
const toggleLike = async (insight) => {
  if (likingSet.has(insight.id)) return
  likingSet.add(insight.id)

  try {
    const res = await api.post('/api/viz/like', {
      insight_id: insight.id,
      device_id: getDeviceId()
    })

    if (res.success) {
      likedInsights.value.add(insight.id)
      insight.likes = res.total_likes
      emit('like-updated', { insightId: insight.id, totalLikes: res.total_likes })
    } else if (res.liked) {
      likedInsights.value.add(insight.id)
    }
  } catch (err) {
    console.error('点赞失败:', err)
  } finally {
    setTimeout(() => likingSet.delete(insight.id), 1000)
  }
}

/**
 * 点击事件处理（移动端动效）
 */
const handleClick = () => {
  clickActive.value = true
  clickTimer = setTimeout(() => {
    clickActive.value = false
  }, 150)
}

/**
 * Touch事件处理（移动端动效）
 * AI维护注意点：touch和click事件可能同时触发，需区分
 */
let touchTimer = null
const touchStart = () => {
  touchActive.value = true
  touchTimer = Date.now()
  
  // 启动长按检测（500ms）
  longPressTimer = setTimeout(() => {
    longPressActive.value = true
  }, 500)
}

const touchEnd = () => {
  const touchDuration = Date.now() - touchTimer
  touchActive.value = false
  
  // 清除长按定时器
  if (longPressTimer) {
    clearTimeout(longPressTimer)
    longPressTimer = null
  }
  
  // 短按（小于500ms）不触发长按
  if (touchDuration < 500) {
    longPressActive.value = false
  }
}

const touchCancel = () => {
  touchActive.value = false
  longPressActive.value = false
  if (longPressTimer) {
    clearTimeout(longPressTimer)
    longPressTimer = null
  }
}

/**
 * 长按处理
 */
const handleLongPress = () => {
  longPressActive.value = true
  // 长按1秒后自动取消
  setTimeout(() => {
    longPressActive.value = false
  }, 1000)
}

/**
 * 触发头像上传（阻止事件冒泡）
 */
const triggerAvatarUpload = () => {
  // 在移动端，点击头像区域触发上传
  // PC端由input元素处理
}

/**
 * 头像上传
 */
const handleAvatarUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

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
    const res = await api.post(`/api/viz/upload-avatar/${props.sharer.name}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    if (res.success) {
      emit('avatar-updated', { name: props.sharer.name, url: res.avatar_url })
      alert('头像上传成功！')
    }
  } catch (err) {
    console.error('上传失败:', err)
    alert('上传失败，请重试')
  }
}
</script>

<style scoped>
.person-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

/* PC端hover效果 */
@media (hover: hover) {
  .person-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  }
}

/* 移动端click效果 */
.person-card.click-active {
  transform: scale(0.95);
  background: #f8f9fa;
}

/* 移动端long-press效果 */
.person-card.long-press-active {
  transform: scale(1.02);
  box-shadow: 0 0 0 3px rgba(25, 118, 210, 0.3);
}

/* 长按提示 */
.long-press-hint {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 12px;
  pointer-events: none;
  animation: fadeInOut 0.5s ease;
}

@keyframes fadeInOut {
  0% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
  50% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
  100% { opacity: 0; transform: translate(-50%, -50%) scale(0.9); }
}

/* 卡片头部 */
.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.avatar-wrapper {
  position: relative;
  width: 56px;
  height: 56px;
  flex-shrink: 0;
}

.avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  background: #f5f5f5;
}

.avatar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.avatar-wrapper:hover .avatar-overlay {
  opacity: 1;
}

.avatar-overlay span {
  color: white;
  font-size: 12px;
  text-align: center;
}

.avatar-input {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.sharer-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.name {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.emoji {
  font-size: 20px;
}

/* 干货列表 */
.insights-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.insight-item {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  transition: all 0.2s;
  cursor: pointer;
}

.insight-item:hover {
  background: #f0f2f5;
}

.insight-item.liked {
  background: #fff3f5;
  border-left: 3px solid #ff6b6b;
}

.insight-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
}

.topic {
  font-weight: 600;
  color: var(--primary-color);
  font-size: 14px;
  line-height: 1.4;
}

.content {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: #555;
  white-space: pre-wrap;
}

/* 点赞按钮 */
.like-wrapper {
  flex-shrink: 0;
}

.like-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 13px;
}

.like-btn:hover {
  border-color: #ff6b6b;
  background: #fff5f5;
}

.like-btn.active {
  border-color: #ff6b6b;
  background: #ffebee;
}

.heart {
  font-size: 14px;
}

.count {
  color: #666;
  font-weight: 500;
}

.like-btn.active .count {
  color: #ff6b6b;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .person-card {
    padding: 16px;
  }
  
  .avatar-wrapper {
    width: 48px;
    height: 48px;
  }
  
  .name {
    font-size: 16px;
  }
  
  .emoji {
    font-size: 18px;
  }
  
  .insight-item {
    padding: 10px;
  }
  
  .topic {
    font-size: 13px;
  }
  
  .content {
    font-size: 12px;
  }
  
  .like-btn {
    padding: 4px 10px;
    font-size: 12px;
  }
}
</style>