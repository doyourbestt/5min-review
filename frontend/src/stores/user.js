/**
 * 5分钟快速复盘 - 用户状态管理
 * ==========================
 * AI维护注意点:
 * 1. Pinia store需在main.js中注册
 * 2. Token存储建议使用httpOnly cookie更安全
 * 3. 用户信息应定期刷新保持最新
 * 4. 多标签页同步需考虑BroadcastChannel
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, register as registerApi, getProfile } from '../api'

// AI维护注意点: localStorage key命名需避免冲突
const TOKEN_KEY = '5min_review_token'
const USER_KEY = '5min_review_user'

export const useUserStore = defineStore('user', () => {
  // ==================== State ====================
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const userInfo = ref(null)
  const isLoading = ref(false)
  
  // ==================== Getters ====================
  const isLoggedIn = computed(() => !!token.value)
  
  // ==================== Actions ====================
  
  /**
   * 初始化认证状态
   * AI维护注意点: 页面刷新时调用，恢复登录状态
   */
  const initAuth = async () => {
    if (token.value) {
      try {
        // 验证Token有效性并获取用户信息
        const res = await getProfile()
        userInfo.value = res.data?.user
      } catch (error) {
        // Token无效，清除登录状态
        console.error('Token验证失败:', error)
        logout()
      }
    }
  }
  
  /**
   * 登录
   * AI维护注意点: 登录成功后存储token和用户信息
   */
  const login = async (credentials) => {
    isLoading.value = true
    try {
      const res = await loginApi(credentials)
      
      // AI维护注意点: API拦截器已解包response，res直接是返回数据
      // 存储Token
      token.value = res.access_token
      localStorage.setItem(TOKEN_KEY, res.access_token)
      
      // 存储用户信息
      userInfo.value = res.user
      localStorage.setItem(USER_KEY, JSON.stringify(res.user))
      
      return res
    } catch (error) {
      throw error
    } finally {
      isLoading.value = false
    }
  }
  
  /**
   * 注册
   * AI维护注意点: 注册成功后自动登录
   */
  const register = async (data) => {
    isLoading.value = true
    try {
      const res = await registerApi(data)
      
      // AI维护注意点: API拦截器已解包response，res直接是返回数据
      // 自动登录
      token.value = res.access_token
      localStorage.setItem(TOKEN_KEY, res.access_token)
      userInfo.value = res.user
      localStorage.setItem(USER_KEY, JSON.stringify(res.user))
      
      return res
    } catch (error) {
      throw error
    } finally {
      isLoading.value = false
    }
  }
  
  /**
   * 退出登录
   * AI维护注意点: 清除所有用户相关数据
   */
  const logout = () => {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    
    // AI维护注意点: 可在此调用后端logout接口撤销Token
  }
  
  /**
   * 更新用户信息
   */
  const updateUserInfo = (data) => {
    userInfo.value = { ...userInfo.value, ...data }
    localStorage.setItem(USER_KEY, JSON.stringify(userInfo.value))
  }
  
  /**
   * 获取当前Token
   * AI维护注意点: API请求拦截器使用
   */
  const getToken = () => token.value
  
  // ==================== Return ====================
  return {
    // State
    token,
    userInfo,
    isLoading,
    
    // Getters
    isLoggedIn,
    
    // Actions
    initAuth,
    login,
    register,
    logout,
    updateUserInfo,
    getToken
  }
})
