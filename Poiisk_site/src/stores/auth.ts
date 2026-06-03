import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, type User } from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('access_token'))

  const isAuthenticated = computed(() => !!token.value)

  async function register(email: string, password: string) {
    const response = await authApi.register(email, password)
    return response.data
  }

  async function login(email: string, password: string) {
    const response = await authApi.login(email, password)
    token.value = response.data.access_token
    user.value = response.data.user
    localStorage.setItem('access_token', token.value)
    return response.data
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('access_token')
  }

  return { user, token, isAuthenticated, register, login, logout }
})