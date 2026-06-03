import axios from 'axios'

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  headers: {
    'Content-Type': 'application/json',
    withCredentials: true,  
  },
})

// Автоматически добавляем токен к запросам
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Интерсептор для обработки ошибок
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Не редиректим автоматически — пусть компонент сам решит
    if (error.response?.status === 401) {
      console.warn('401 Unauthorized')
    }
    return Promise.reject(error)
  }
)

export default api

// Типы
export interface User {
  id: number
  email: string
}

export interface ChatMessage {
  answer: string
  state: {
    role: string | null
    skills: string[]
    location: string | null
    level: string | null
    search_ready: boolean
  }
  vacancies?: Vacancy[]
}

export interface Vacancy {
  name: string
  company: string
  url: string
  snippet: string
  salary?: string
  relevance_score?: number
  relevance_reason?: string
}

// API методы
export const authApi = {
  register: (email: string, password: string) =>
    api.post('/auth/register', { email, password }),

  login: async (email: string, password: string) => {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)

    try {
      const response = await api.post('/auth/login', formData.toString(), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      })
      return response
    } catch (error) {
      console.error('API login error:', error)
      throw error
    }
  },
}

export const chatApi = {
  sendMessage: (text: string) =>
    api.post<ChatMessage>('/chat', { text }),
}