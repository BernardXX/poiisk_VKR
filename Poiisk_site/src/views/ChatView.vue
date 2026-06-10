<template>
  <div class="chat-page">
    <!-- Сайдбар -->
    <ChatSidebar
      ref="sidebarRef"
      @chat-select="handleChatSelect"
      @chat-create="handleChatCreate"
      @chat-delete="handleChatDelete"
    />
    
    <!-- Основная область -->
    <div class="chat-main">
      <header class="chat-header">
        <h2>{{ currentTitle }}</h2>
      </header>

      <div class="messages-container" ref="messagesContainer">
        <div v-if="messages.length === 0 && !isLoading" class="welcome-message">
          <h3>👋 Начни диалог</h3>
          <p>Расскажи, кого ты ищешь, какие у тебя навыки и в каком городе хочешь работать.</p>
        </div>

        <div v-for="(msg, index) in messages" :key="index" class="message-wrapper" :class="msg.role">
          <div class="message-bubble">
            <div 
              v-if="msg.role === 'assistant'" 
              class="message-content markdown-body" 
              v-html="parseMarkdown(msg.content)"
            ></div>
            <p v-else class="message-content">{{ msg.content }}</p>
            
            <div v-if="msg.metadata?.vacancies" class="vacancies-list">
              <VacancyCard v-for="(vacancy, idx) in msg.metadata.vacancies" :key="idx" :vacancy="vacancy" />
            </div>
          </div>
          <span class="message-time">{{ formatTime(msg.created_at) }}</span>
        </div>

        <div v-if="isLoading" class="typing-indicator">
          <span></span> <span></span> <span></span>
        </div>
      </div>

      <!-- Кнопка поиска вакансий -->
      <div class="job-search-prompt">
        <button 
          @click="startJobSearch" 
          class="btn-job-search"
          :disabled="!isProfileComplete || isCheckingProfile"
          :title="!isProfileComplete ? missingProfileFields.join(', ') : ''"
        >
          <span v-if="isCheckingProfile" class="btn-loading">⏳ Проверка...</span>
          <span v-else-if="!isProfileComplete">⚠️ Заполните профиль</span>
          <span v-else>💼 Начать поиск вакансий</span>
        </button>
        
      </div>

      <div class="input-container">
        <form @submit.prevent="handleSend" class="input-form">
          <input
            v-model="inputText"
            type="text"
            placeholder="Напишите сообщение..."
            :disabled="isLoading"
            class="message-input"
          />
          <button type="submit" :disabled="!inputText.trim() || isLoading" class="send-button">➤</button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, computed } from 'vue'
import ChatSidebar from '@/components/ChatSidebar.vue'
import VacancyCard from '@/components/VacancyCard.vue'
import { parseMarkdown } from '@/utils/markdown'

const sidebarRef = ref<InstanceType<typeof ChatSidebar> | null>(null)
const messagesContainer = ref<HTMLElement | null>(null)

const currentSessionId = ref<number | null>(null)
const currentTitle = ref('Новый диалог')
const messages = ref<any[]>([])
const inputText = ref('')
const isLoading = ref(false)
const showJobSearch = ref(false)

// Состояние для проверки профиля
const isProfileComplete = ref(false)
const isCheckingProfile = ref(true)
const missingProfileFields = ref<string[]>([])

const userId = computed(() => {
  const id = localStorage.getItem('user_id')
  return id ? parseInt(id, 10) : 1
})

// Функция проверки заполненности профиля
async function checkProfileCompleteness() {
  isCheckingProfile.value = true
  try {
    const uid = userId.value
    const response = await fetch(`http://127.0.0.1:8000/api/profile/?user_id=${uid}`)
    
    if (response.ok) {
      const profile = await response.json()
      
      // Список обязательных полей
      const requiredFields = [
        { key: 'full_name', label: 'ФИО' },
        { key: 'desired_role', label: 'Желаемая должность' },
        { key: 'location', label: 'Город/формат работы' },
        { key: 'skills', label: 'Навыки', check: (val: any) => val && Object.keys(val).length > 0 }
      ]
      
      const missing = requiredFields
        .filter(field => {
          const value = profile[field.key]
          if (field.check) {
            return !field.check(value)
          }
          return !value || value === `[${field.label}]` || value === `[${field.label.toUpperCase()}]`
        })
        .map(field => field.label)
      
      missingProfileFields.value = missing
      isProfileComplete.value = missing.length === 0
    } else {
      isProfileComplete.value = false
      missingProfileFields.value = ['Не удалось загрузить профиль']
    }
  } catch (err) {
    console.error('Profile check error:', err)
    isProfileComplete.value = false
    missingProfileFields.value = ['Ошибка соединения']
  } finally {
    isCheckingProfile.value = false
  }
}

// Функция поиска вакансий с сохранением в чат
async function startJobSearch() {
  showJobSearch.value = true
  isLoading.value = true
  
  try {
    const uid = userId.value
    
    // Показываем сообщение о начале поиска
    messages.value.push({
      role: 'assistant',
      content: '🔍 Анализирую ваш профиль и ищу подходящие вакансии на сайтах...',
      created_at: new Date().toISOString()
    })
    await nextTick(() => { 
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight 
      }
    })
    
    // Вызываем новый эндпоинт
    const formData = new FormData()
    formData.append('user_id', uid.toString())
    if (currentSessionId.value) {
      formData.append('session_id', currentSessionId.value.toString())
    }
    
    const response = await fetch('http://127.0.0.1:8000/api/vacancies/search-and-save', {
      method: 'POST',
      body: formData
    })
    
    if (response.ok) {
      const data = await response.json()
      
      // Загружаем обновлённую историю чата
      if (data.session_id) {
        currentSessionId.value = data.session_id
        localStorage.setItem('activeSessionId', String(data.session_id))
        await loadChatMessages(data.session_id)
      }
      
    } else {
      const error = await response.json()
      alert(`❌ Ошибка: ${error.detail}`)
    }
  } catch (err) {
    console.error('Job search error:', err)
    alert('❌ Ошибка при поиске вакансий')
  } finally {
    isLoading.value = false
    showJobSearch.value = false
  }
}

// Поиск вакансий с матчингом
async function searchVacancies() {
  isLoading.value = true
  showJobSearch.value = true
  
  try {
    const uid = userId.value
    
    // Добавляем сообщение о начале поиска
    messages.value.push({
      role: 'assistant',
      content: '🔍 Анализирую ваш профиль и ищу подходящие вакансии сайтах...',
      created_at: new Date().toISOString()
    })
    await nextTick(() => { 
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight 
      }
    })
    
    const response = await fetch(`http://127.0.0.1:8000/api/vacancies/search?user_id=${uid}`)
    
    if (!response.ok) {
      throw new Error(`Ошибка: ${response.status}`)
    }
    
    const data = await response.json()
    
    if (data.vacancies && data.vacancies.length > 0) {
      // Добавляем результат поиска
      messages.value.push({
        role: 'assistant',
        content: `✅ Найдено ${data.vacancies.length} подходящих вакансий! Вот лучшие匹配и на основе вашего профиля:`,
        metadata: { vacancies: data.vacancies },
        created_at: new Date().toISOString()
      })
    } else {
      messages.value.push({
        role: 'assistant',
        content: '😔 К сожалению, подходящих вакансий не найдено. Попробуйте расширить критерии поиска или обновить навыки в профиле.',
        created_at: new Date().toISOString()
      })
    }
    
    await nextTick(() => { 
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight 
      }
    })
    
  } catch (err: any) {
    console.error(err)
    messages.value.push({
      role: 'assistant',
      content: `❌ Ошибка при поиске вакансий: ${err.message}`,
      created_at: new Date().toISOString()
    })
  } finally {
    isLoading.value = false
  }
}

// Проверяем профиль при загрузке компонента
onMounted(async () => {
  await sidebarRef.value?.loadChats()
  await checkProfileCompleteness() 
  
  const savedSessionId = localStorage.getItem('activeSessionId')
  if (savedSessionId) {
    currentSessionId.value = parseInt(savedSessionId, 10)
    await loadChatMessages(currentSessionId.value, true)
  }
})

async function handleChatSelect(sessionId: number) {
  currentSessionId.value = sessionId
  localStorage.setItem('activeSessionId', String(sessionId))
  await loadChatMessages(sessionId)
}

function handleChatCreate(newChat: any) {
  currentSessionId.value = newChat.session_id
  currentTitle.value = newChat.title
  messages.value = []
  showJobSearch.value = false
  localStorage.setItem('activeSessionId', String(newChat.session_id))
}

function handleChatDelete(deletedId: number) {
  if (currentSessionId.value === deletedId) {
    currentSessionId.value = null
    messages.value = []
    currentTitle.value = 'Новый диалог'
    showJobSearch.value = false
    localStorage.removeItem('activeSessionId')
  }
}

async function loadChatMessages(sessionId: number, silentError = false) {
  try {
    const uid = userId.value
    const response = await fetch(`http://127.0.0.1:8000/api/chats/${sessionId}/messages?user_id=${uid}`)

    if (response.ok) {
      messages.value = await response.json()
      await nextTick(() => {
        if (messagesContainer.value) messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      })
    } else if (response.status === 403) {
      currentSessionId.value = null
      messages.value = []
      localStorage.removeItem('activeSessionId')
      if (!silentError) alert('Доступ запрещен: этот чат принадлежит другому пользователю')
    }
  } catch (err) {
    console.error('Failed to load messages:', err)
  }
}

async function handleSend() {
  if (!inputText.value.trim()) return

  isLoading.value = true
  const userText = inputText.value
  inputText.value = ''

  try {
    messages.value.push({ role: 'user', content: userText, created_at: new Date().toISOString() })
    await nextTick(() => { if (messagesContainer.value) messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight })

    const uid = userId.value
    const sessionIdParam = currentSessionId.value ? `&session_id=${currentSessionId.value}` : ''
    const url = `http://127.0.0.1:8000/chat?user_id=${uid}${sessionIdParam}`

    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: userText }),
    })

    if (!response.ok) throw new Error(`Ошибка: ${response.status}`)
    const data = await response.json()

    if (!currentSessionId.value && data.session_id) {
      currentSessionId.value = data.session_id
      localStorage.setItem('activeSessionId', String(data.session_id))
      await sidebarRef.value?.loadChats()
    }

    messages.value.push({ 
      role: 'assistant', 
      content: data.answer, 
      metadata: data.metadata || null, 
      created_at: new Date().toISOString() 
    })
    await sidebarRef.value?.loadChats()
    await nextTick(() => { if (messagesContainer.value) messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight })

  } catch (err: any) {
    console.error(err)
    if (messages.value.length > 0) messages.value.pop()
    alert('Ошибка: ' + err.message)
  } finally {
    isLoading.value = false
  }
}

function formatTime(dateStr: string): string {
  return new Date(dateStr).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.chat-page {
  display: flex;
  height: calc(100vh - 64px);
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f7fafc;
}

.chat-header {
  padding: 16px 24px; 
  background: white;
  border-bottom: 1px solid #e2e8f0;
}

.chat-header h2 {
  margin: 0;
  color: #2d3748;
  font-size: 1.2rem;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.welcome-message {
  text-align: center;
  padding: 60px 20px;
  color: #4a5568;
}

.welcome-message h3 {
  font-size: 1.5rem;
  margin-bottom: 12px;
  color: #2d3748;
}

.message-wrapper {
  display: flex;
  flex-direction: column;
  max-width: 85%;
}

.message-wrapper.user {
  align-self: flex-end;
}

.message-wrapper.assistant {
  align-self: flex-start;
}

.message-bubble {
  padding: 14px 18px;
  border-radius: 16px;
  word-wrap: break-word;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.message-wrapper.user .message-bubble {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.message-wrapper.assistant .message-bubble {
  background: white;
  border: 1px solid #e2e8f0;
  border-bottom-left-radius: 4px;
}

.message-content {
  margin: 0;
  line-height: 1.6;
  white-space: pre-wrap;
}

.markdown-body {
  white-space: normal;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  margin-top: 12px;
  margin-bottom: 8px;
  font-weight: 600;
  color: #2d3748;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 8px 0 8px 24px;
  padding-left: 0;
}

.markdown-body :deep(li) {
  margin-bottom: 4px;
}

.markdown-body :deep(strong) {
  font-weight: 700;
  color: #2d3748;
}

.markdown-body :deep(em) {
  font-style: italic;
}

.markdown-body :deep(code) {
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.9em;
  color: #d63384;
}

.markdown-body :deep(pre) {
  background: #f1f5f9;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
}

.markdown-body :deep(pre code) {
  background: transparent;
  padding: 0;
  color: inherit;
}

.markdown-body :deep(blockquote) {
  border-left: 3px solid #667eea;
  padding-left: 12px;
  margin: 12px 0;
  color: #4a5568;
  font-style: italic;
}

.message-time {
  font-size: 0.75rem;
  color: #a0aec0;
  margin-top: 4px;
  padding: 0 4px;
}

.vacancies-list {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 14px 18px;
  background: white;
  border-radius: 16px;
  width: fit-content;
  align-self: flex-start;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #a0aec0;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-10px); }
}

.input-container {
  padding: 20px 24px;
  background: white;
  border-top: 1px solid #e2e8f0;
}

.input-form {
  display: flex;
  gap: 12px;
  max-width: 900px;
  margin: 0 auto;
}

.message-input {
  flex: 1;
  padding: 14px 18px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s;
}

.message-input:focus {
  border-color: #667eea;
}

.message-input:disabled {
  background: #f7fafc;
  cursor: not-allowed;
}

.send-button {
  padding: 14px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1.2rem;
  cursor: pointer; 
  transition: transform 0.2s, opacity 0.2s;
}

.send-button:hover:not(:disabled) {
  transform: scale(1.05);
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.messages-container::-webkit-scrollbar {
  width: 8px;
}

.messages-container::-webkit-scrollbar-track {
  background: #f7fafc;
}

.messages-container::-webkit-scrollbar-thumb { 
  background: #cbd5e0;
  border-radius: 4px;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: #a0aec0;
}

.job-search-prompt {
  padding: 16px 24px;
  background: #f7fafc;
  border-top: 1px solid #e2e8f0;
  text-align: center;
}

.btn-job-search {
  padding: 12px 32px;
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(72, 187, 120, 0.3);
}

.btn-job-search:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(72, 187, 120, 0.4);
}

/* Стили для списка вакансий */
.vacancies-list {
  margin-top: 16px;
  display: grid;
  gap: 12px;
}

.btn-job-search:disabled {
  background: #cbd5e0;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
  opacity: 0.8;
}

.btn-job-search:disabled:hover {
  transform: none;
  box-shadow: none;
}

.btn-loading {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.profile-hint {
  margin-top: 8px;
  font-size: 0.85rem;
  color: #e53e3e;
  text-align: center;
  padding: 4px 8px;
  background: #fff5f5;
  border-radius: 6px;
  border-left: 3px solid #fc8181;
}

.btn-job-search:disabled[title]:hover::after {
  content: attr(title);
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: #2d3748;
  color: white;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 0.8rem;
  white-space: nowrap;
  z-index: 100;
  margin-bottom: 4px;
}
</style>