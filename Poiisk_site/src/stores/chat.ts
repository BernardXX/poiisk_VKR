import { defineStore } from 'pinia'
import { ref } from 'vue'
import { chatApi, type ChatMessage, type Vacancy } from '@/api/client'

export interface Message {
  role: 'user' | 'assistant'
  content: string
  vacancies?: Vacancy[]
  timestamp: Date
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<Message[]>([])
  const isLoading = ref(false)
  const state = ref({
    role: null as string | null,
    skills: [] as string[],
    location: null as string | null,
    level: null as string | null,
    search_ready: false,
  })

  async function sendMessage(text: string) {
    isLoading.value = true
    
    // Добавляем сообщение пользователя
    messages.value.push({
      role: 'user',
      content: text,
      timestamp: new Date(),
    })

    try {
      const response = await chatApi.sendMessage(text)
      
      // Обновляем состояние
      state.value = response.data.state
      
      // Добавляем ответ бота
      messages.value.push({
        role: 'assistant',
        content: response.data.answer,
        vacancies: response.data.vacancies,
        timestamp: new Date(),
      })
      
      return response.data
    } catch (error) {
      console.error('Ошибка отправки сообщения:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  function clearChat() {
    messages.value = []
  }

  return { messages, isLoading, state, sendMessage, clearChat }
})