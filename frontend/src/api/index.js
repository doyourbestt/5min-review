/**
 * 5分钟快速复盘 - API接口封装
 * ==========================
 * AI维护注意点:
 * 1. axios实例配置集中管理
 * 2. 请求/响应拦截器统一处理错误
 * 3. Token过期自动刷新(待实现)
 * 4. API路径需与后端路由保持一致
 */

import axios from 'axios'

// AI维护注意点: 基础URL从环境变量获取，支持多环境
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

// 直接从localStorage获取token，避免在拦截器中使用store(此时Pinia可能未初始化)
const TOKEN_KEY = '5min_review_token'
const getToken = () => localStorage.getItem(TOKEN_KEY) || ''

// 创建axios实例
const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000, // 10秒超时
  headers: {
    'Content-Type': 'application/json'
  }
})

// ==================== 请求拦截器 ====================
/**
 * AI维护注意点:
 * 1. 自动添加Authorization头
 * 2. 可在此添加请求日志
 * 3. 请求前显示loading状态
 */
api.interceptors.request.use(
  (config) => {
    // 获取Token
    const token = getToken()
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // AI维护注意点: 可在此添加全局loading
    // console.log('Request:', config.url)
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// ==================== 响应拦截器 ====================
/**
 * AI维护注意点:
 * 1. 统一错误处理
 * 2. Token过期自动跳转登录
 * 3. 数据格式统一转换
 */
api.interceptors.response.use(
  (response) => {
    // 直接返回响应数据
    return response.data
  },
  (error) => {
    // 错误处理
    if (error.response) {
      const { status, data } = error.response
      
      // 401: 未认证或Token过期
      if (status === 401) {
        // 清除token并跳转到登录页
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem('5min_review_user')
        window.location.href = '/login'
        return Promise.reject(new Error('登录已过期，请重新登录'))
      }
      
      // 403: 无权限
      if (status === 403) {
        return Promise.reject(new Error(data.error || '无权限执行此操作'))
      }
      
      // 其他错误
      return Promise.reject(new Error(data.error || '请求失败'))
    }
    
    // 网络错误
    if (error.request) {
      return Promise.reject(new Error('网络错误，请检查网络连接'))
    }
    
    return Promise.reject(error)
  }
)

// ==================== API方法导出 ====================

// 认证相关
export const login = (data) => api.post('/auth/login', data)
export const register = (data) => api.post('/auth/register', data)
export const getProfile = () => api.get('/auth/profile')
export const updateProfile = (data) => api.put('/auth/profile', data)

// 模板相关
export const getTemplates = (params) => api.get('/templates', { params })
export const getTemplate = (id) => api.get(`/templates/${id}`)
export const createTemplate = (data) => api.post('/templates', data)
export const updateTemplate = (id, data) => api.put(`/templates/${id}`, data)
export const deleteTemplate = (id) => api.delete(`/templates/${id}`)

// 复盘相关
export const getReviews = (params) => api.get('/reviews', { params })
export const getReview = (id) => api.get(`/reviews/${id}`)
export const createReview = (data) => api.post('/reviews', data)
export const deleteReview = (id) => api.delete(`/reviews/${id}`)
export const getTodayReview = () => api.get('/reviews/today')
export const getRecentReviews = (params) => api.get('/reviews', { params })
export const getCheckinStatus = () => api.get('/reviews/checkin')

// 统计相关
export const getOverview = () => api.get('/stats/overview')
export const getCalendarStats = (params) => api.get('/stats/calendar', { params })
export const getTrends = (params) => api.get('/stats/trends', { params })
export const getFieldStats = (params) => api.get('/stats/fields', { params })
export const getTemplateUsage = () => api.get('/stats/templates')

// 可视化相关
export const parseMarkdown = (data) => api.post('/viz/parse', data)
export const saveReview = (data) => api.post('/viz/save', data)
export const getReviewByDate = (date) => api.get(`/viz/reviews/${date}`)
export const getAvailableDates = () => api.get('/viz/dates')
export const uploadAvatar = (sharerName, file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post(`/viz/upload-avatar/${sharerName}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
export const likeInsight = (data) => api.post('/viz/like', data)
export const getLikesByInsight = (insightId) => api.get(`/viz/likes/${insightId}`)
export const getLikesByTopic = (topic) => api.get('/viz/likes/by-topic', { params: { topic } })
export const getLikesBySharer = (sharerName) => api.get(`/viz/likes/by-sharer/${sharerName}`)

// 默认导出实例
export default api
