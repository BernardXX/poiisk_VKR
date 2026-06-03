<template>
  <aside class="chat-sidebar" :class="{ collapsed: isCollapsed }">
    <button @click="toggleSidebar" class="toggle-btn">
      {{ isCollapsed ? '▶' : '◀' }}
    </button>

    <button @click="createNewChat" class="new-chat-btn">
      <span class="btn-icon">+</span>
      <span class="btn-text" v-if="!isCollapsed">Новый чат</span>
    </button>

    <div class="chats-list">
      <div v-for="chat in chats" :key="chat.session_id" class="chat-item" :class="{ active: chat.session_id === currentSessionId }" @click="selectChat(chat.session_id)">
        <span class="chat-title">{{ chat.title }}</span>
        <button @click.stop="deleteChat(chat.session_id)" class="delete-btn" title="Удалить чат">✕</button>
      </div>
      
      <div v-if="chats.length === 0" class="empty-state">
        <p>Нет чатов</p>
        <p class="hint">Создай первый чат кнопкой выше</p>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, onMounted, defineEmits } from 'vue'

const emit = defineEmits(['chat-select', 'chat-create', 'chat-delete'])

const isCollapsed = ref(false)
const chats = ref<any[]>([])
const currentSessionId = ref<number | null>(null)

function getUserId(): number {
  const raw = localStorage.getItem('user_id')
  if (!raw) return 1 
  const parsed = parseInt(raw, 10)
  return isNaN(parsed) ? 1 : parsed
}

async function loadChats() {
  try {
    const uid = getUserId()
    const response = await fetch(`http://127.0.0.1:8000/api/chats?user_id=${uid}`)
    if (response.ok) {
      chats.value = await response.json()
    }
  } catch (err) {
    console.error('Failed to load chats:', err)
  }
}

async function createNewChat() {
  try {
    const uid = getUserId()
    
    const response = await fetch(`http://127.0.0.1:8000/api/chats?user_id=${uid}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: 'Новый диалог' }),
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `Ошибка сервера: ${response.status}`)
    }
    
    const newChat = await response.json()
    await loadChats()
    selectChat(newChat.session_id)
    emit('chat-create', newChat)
  } catch (err: any) {
    console.error('Failed to create chat:', err)
    alert('Не удалось создать чат: ' + err.message)
  }
}

function selectChat(sessionId: number) {
  currentSessionId.value = sessionId
  emit('chat-select', sessionId)
}

async function deleteChat(sessionId: number) {
  if (!confirm('Удалить этот чат?')) return
  
  try {
    const uid = getUserId()
    const response = await fetch(`http://127.0.0.1:8000/api/chats/${sessionId}?user_id=${uid}`, { method: 'DELETE' })
    
    if (!response.ok) throw new Error(`Ошибка: ${response.status}`)
    
    await loadChats()
    emit('chat-delete', sessionId)
    if (currentSessionId.value === sessionId) currentSessionId.value = null
  } catch (err: any) {
    console.error('Failed to delete chat:', err)
    alert('Не удалось удалить чат: ' + err.message)
  }
}

function toggleSidebar() {
  isCollapsed.value = !isCollapsed.value
}

onMounted(() => {
  loadChats()
})

defineExpose({ loadChats })
</script>

<style scoped>
.chat-sidebar {
  width: 280px;
  background: #1a202c;
  color: white;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  position: relative;
}

.chat-sidebar.collapsed {
  width: 60px;
}

.toggle-btn {
  position: absolute;
  top: 12px;
  right: -12px;
  width: 24px;
  height: 24px;
  background: #2d3748;
  border: none;
  border-radius: 4px;
  color: white;
  cursor: pointer;
  z-index: 10;
  font-size: 0.8rem;
}

.new-chat-btn {
  margin: 16px;
  padding: 12px;
  background: #48bb78;
  border: none;
  border-radius: 8px;
  color: white;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
  transition: all 0.3s ease;
  overflow: hidden;
  white-space: nowrap;
}

.new-chat-btn .btn-icon {
  font-size: 1.2rem;
  font-weight: bold;
  min-width: 20px;
  text-align: center;
  flex-shrink: 0;
}

.new-chat-btn .btn-text {
  opacity: 1;
  transition: opacity 0.2s ease;
}

.chat-sidebar.collapsed .new-chat-btn {
  justify-content: center;
  padding: 12px;
  width: calc(100% - 32px);
}

.chat-sidebar.collapsed .new-chat-btn .btn-text {
  display: none; 
}

.chat-sidebar.collapsed .new-chat-btn .btn-icon {
  margin: 0;
}

.chats-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 12px;
}

.chat-item {
  padding: 12px;
  margin-bottom: 4px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  transition: background 0.2s;
}

.chat-item:hover {
  background: #2d3748;
}

.chat-item.active {
  background: #4a5568;
}

.chat-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.9rem;
}

.delete-btn {
  opacity: 0;
  background: transparent;
  border: none;
  color: #e53e3e;
  cursor: pointer;
  padding: 4px 8px;
  font-size: 1rem;
  transition: opacity 0.2s;
}

.chat-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: #fed7d7;
  border-radius: 4px;
}

.empty-state {
  text-align: center;
  padding: 32px 16px;
  color: #718096;
}

.empty-state .hint {
  font-size: 0.85rem;
  margin-top: 8px;
}

/* Скроллбар */
.chats-list::-webkit-scrollbar {
  width: 6px;
}

.chats-list::-webkit-scrollbar-track {
  background: #1a202c;
}

.chats-list::-webkit-scrollbar-thumb {
  background: #4a5568;
  border-radius: 3px;
}

.chats-list::-webkit-scrollbar-thumb:hover {
  background: #718096;
}
</style>