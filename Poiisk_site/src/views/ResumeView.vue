<template>
  <div class="resume-page">
    <div class="resume-header">
      <h1>📄 Моё резюме</h1>
      <button @click="showCreateModal = true" class="btn-create">+ Создать резюме</button>
    </div>

    <!-- Список резюме -->
    <div v-if="resumes.length > 0" class="resumes-list">
      <div v-for="resume in resumes" :key="resume.resume_id" class="resume-card" :class="{ primary: resume.is_primary }">
        <div class="resume-info">
          <h3>{{ resume.title }}</h3>
          <div class="resume-meta">
            <span class="status" :class="resume.status">{{ resume.status === 'draft' ? 'Черновик' : 'Готовое' }}</span>
            <span v-if="resume.is_primary" class="primary-badge">Основное</span>
            <span class="date">Обновлено: {{ formatDate(resume.updated_at) }}</span>
          </div>
        </div>
        <div class="resume-actions">
          <button @click="viewResume(resume.resume_id)" class="btn-action">👁 Просмотр</button>
          <button @click="editResume(resume.resume_id)" class="btn-action">✏️ Редактировать</button>
          <button @click="setPrimary(resume.resume_id)" v-if="!resume.is_primary" class="btn-action">⭐ Сделать основным</button>
          <button @click="deleteResume(resume.resume_id)" class="btn-action delete">🗑 Удалить</button>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <p>У вас пока нет резюме</p>
      <button @click="showCreateModal = true" class="btn-create">Создать первое резюме</button>
    </div>

    <!-- Модальное окно: выбор способа создания -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal">
        <h2>Создание резюме</h2>
        <div class="create-options">
          <button @click="selectCreateMethod('upload')" class="option-card">
            <div class="option-icon">📤</div>
            <h3>Загрузить файл</h3>
            <p>PDF или DOCX</p>
          </button>
          <button @click="selectCreateMethod('chat')" class="option-card">
            <div class="option-icon">💬</div>
            <h3>Из истории чата</h3>
            <p>На основе диалога с ИИ</p>
          </button>
          <button @click="selectCreateMethod('project')" class="option-card">
            <div class="option-icon">📁</div>
            <h3>Из проекта</h3>
            <p>Анализ кода проекта</p>
          </button>
        </div>
        <button @click="showCreateModal = false" class="btn-cancel">Отмена</button>
      </div>
    </div>

    <!-- Модальное окно: загрузка файла -->
    <div v-if="createMethod === 'upload'" class="modal-overlay" @click.self="cancelCreate">
      <div class="modal">
        <h2>Загрузка резюме</h2>
        <div class="form-group">
          <label>Название резюме</label>
          <input v-model="resumeTitle" type="text" placeholder="Например: Резюме Frontend разработчика" />
        </div>
        <div class="form-group">
          <label>Файл резюме</label>
          <input type="file" @change="handleFileUpload" accept=".pdf,.docx,.txt" />
          <p class="hint">Разрешены файлы PDF, DOCX, TXT</p>
        </div>
        <div class="modal-actions">
          <button @click="uploadResume" :disabled="!selectedFile || !resumeTitle" class="btn-primary">Загрузить</button>
          <button @click="cancelCreate" class="btn-secondary">Отмена</button>
        </div>
      </div>
    </div>

    <!-- Модальное окно: из чата -->
    <div v-if="createMethod === 'chat'" class="modal-overlay" @click.self="cancelCreate">
      <div class="modal">
        <h2>Создание из истории чата</h2>
        <div class="form-group">
          <label>Название резюме</label>
          <input v-model="resumeTitle" type="text" placeholder="Например: Резюме на основе чата" />
        </div>
        <div class="form-group">
          <label>Выберите чат</label>
          <select v-model="selectedSessionId">
            <option :value="null">Выберите чат...</option>
            <option v-for="chat in chats" :key="chat.session_id" :value="chat.session_id">{{ chat.title }}</option>
          </select>
        </div>
        <div class="modal-actions">
          <button @click="createResumeFromChat" :disabled="!selectedSessionId || !resumeTitle" class="btn-primary">Создать</button>
          <button @click="cancelCreate" class="btn-secondary">Отмена</button>
        </div>
      </div>
    </div>

    <!-- Модальное окно: из проекта (СОЗДАНИЕ) -->
    <div v-if="createMethod === 'project'" class="modal-overlay" @click.self="cancelCreate">
      <div class="modal large">
        <h2>Создание из проекта</h2>
        
        <div class="form-group">
          <label>Название проекта</label>
          <input v-model="resumeTitle" type="text" placeholder="Например: Мой pet-проект" />
        </div>

        <div class="form-group">
          <label>Выберите папку с проектом</label>
          <input 
            type="file" 
            @change="handleProjectFolder" 
            webkitdirectory 
            directory 
            class="folder-input"
            ref="fileInputRef"
          />
          <p class="hint">Выберите папку для анализа структуры</p>
        </div>

        <!-- Отображение структуры папок -->
        <div v-if="projectTree" class="file-tree-container">
          <h3>Структура проекта ({{ selectedFilesCount }} файлов выбрано из {{ totalFilesCount }})</h3>
          
          <div class="tree-controls">
            <button @click="selectAllFiles" class="btn-sm">✓ Выбрать все</button>
            <button @click="deselectAllFiles" class="btn-sm">✗ Снять все</button>
            <button @click="selectCodeOnly" class="btn-sm">💻 Только код</button>
            <button @click="expandAll" class="btn-sm">📂 Развернуть все</button>
            <button @click="collapseAll" class="btn-sm">📁 Свернуть все</button>
          </div>

          <div class="tree-scroll">
            <FileTreeNode 
              v-for="node in projectTree" 
              :key="node.path"
              :node="node"
              :selected-files="selectedFilePaths"
              :expanded-folders="expandedFolders"
              @toggle-file="toggleFile"
              @toggle-folder="toggleFolder"
            />
          </div>
        </div>
        
        <div class="modal-actions">
          <button 
            @click="createResumeFromProject" 
            :disabled="!resumeTitle || selectedFilesCount === 0" 
            class="btn-primary"
          >
            Проанализировать и создать ({{ selectedFilesCount }} файлов)
          </button>
          <button @click="cancelCreate" class="btn-secondary">Отмена</button>
        </div>
      </div>
    </div>

    <!-- Модальное окно: просмотр/редактирование -->
    <div v-if="viewingResume || editingResume" class="modal-overlay" @click.self="closeEditor">
      <div class="modal extra-large">
        <h2>{{ editingResume ? 'Редактирование' : 'Просмотр' }}: {{ viewingResume?.title || editingResume?.title }}</h2>
        
        <!-- Кнопки AI-улучшения (только в режиме редактирования) -->
        <div v-if="editingResume" class="ai-improvement-panel">
          <h3>🤖 AI-помощник</h3>
          <div class="improvement-buttons">
            <button @click="improveResume('professional')" class="btn-ai" :disabled="isAiProcessing">
              ✨ Сделать профессиональнее
            </button>
            <button @click="improveResume('concise')" class="btn-ai" :disabled="isAiProcessing">
              📝 Сделать лаконичнее
            </button>
            <button @click="improveResume('detailed')" class="btn-ai" :disabled="isAiProcessing">
              📊 Добавить деталей
            </button>
            <button @click="improveResume('ats')" class="btn-ai" :disabled="isAiProcessing">
              🎯 Оптимизировать для ATS
            </button>
          </div>
          
          <div class="append-section">
            <h4>➕ Дополнить резюме</h4>
            <div class="append-buttons">
              <button @click="showAppendFromChat = true" class="btn-append">
                💬 Из чата
              </button>
              <button @click="showAppendFromProject = true" class="btn-append">
                📁 Из проекта
              </button>
            </div>
          </div>
          
          <div v-if="isAiProcessing" class="ai-processing">
            <div class="spinner"></div>
            <p>ИИ обрабатывает ваше резюме...</p>
          </div>
        </div>
        
        <div v-if="editingResume" class="editor-controls">
          <input v-model="editingResume.title" type="text" class="edit-title" placeholder="Название резюме" />
          
          <div class="form-row">
            <label>Статус:</label>
            <select v-model="editingResume.status" class="edit-select">
              <option value="draft">Черновик</option>
              <option value="published">Готовое</option>
            </select>
          </div>

          <textarea v-model="editingResume.content" class="edit-content" rows="20" placeholder="Содержимое резюме"></textarea>
        </div>
        
        <div v-else class="resume-content" v-html="formatResumeContent(viewingResume?.content || '')"></div>
        
        <div class="modal-actions">
          <button v-if="editingResume" @click="saveResume" class="btn-primary" :disabled="isAiProcessing">
            💾 Сохранить
          </button>
          <button @click="closeEditor" class="btn-secondary">Закрыть</button>
        </div>
      </div>
    </div>

    <!-- Модальное окно: дополнение из чата -->
    <div v-if="showAppendFromChat" class="modal-overlay" @click.self="showAppendFromChat = false">
      <div class="modal">
        <h2>Дополнить резюме из чата</h2>
        
        <div class="form-group">
          <label>Выберите чат</label>
          <select v-model="appendChatSessionId">
            <option :value="null">Выберите чат...</option>
            <option v-for="chat in chats" :key="chat.session_id" :value="chat.session_id">
              {{ chat.title }}
            </option>
          </select>
        </div>
        
        <div class="form-group">
          <label>Что добавить?</label>
          <select v-model="appendChatType">
            <option value="all">Всё релевантное</option>
            <option value="skills">Навыки</option>
            <option value="experience">Опыт работы</option>
            <option value="projects">Проекты</option>
          </select>
        </div>
        
        <div class="modal-actions">
          <button @click="appendFromChat" :disabled="!appendChatSessionId || isAiProcessing" class="btn-primary">
            {{ isAiProcessing ? 'Обработка...' : 'Дополнить' }}
          </button>
          <button @click="showAppendFromChat = false" class="btn-secondary">Отмена</button>
        </div>
      </div>
    </div>

    <!-- Модальное окно: дополнение из проекта (С ДЕРЕВОМ ФАЙЛОВ) -->
    <div v-if="showAppendFromProject" class="modal-overlay" @click.self="showAppendFromProject = false">
      <div class="modal large">
        <h2>Дополнить резюме из проекта</h2>
        
        <div class="form-group">
          <label>Название проекта</label>
          <input v-model="appendProjectName" type="text" placeholder="Например: Интернет-магазин" />
        </div>

        <div class="form-group">
          <label>Выберите папку с проектом</label>
          <input 
            type="file" 
            @change="handleAppendProjectFolder" 
            webkitdirectory 
            directory 
            class="folder-input"
            ref="appendFileInputRef"
          />
          <p class="hint">Выберите папку для анализа структуры</p>
        </div>

        <!-- Отображение структуры папок (КАК ПРИ СОЗДАНИИ) -->
        <div v-if="appendProjectTree" class="file-tree-container">
          <h3>Структура проекта ({{ appendSelectedFilesCount }} файлов выбрано из {{ appendTotalFilesCount }})</h3>
          
          <div class="tree-controls">
            <button @click="appendSelectAllFiles" class="btn-sm">✓ Выбрать все</button>
            <button @click="appendDeselectAllFiles" class="btn-sm">✗ Снять все</button>
            <button @click="appendSelectCodeOnly" class="btn-sm">💻 Только код</button>
          </div>

          <div class="tree-scroll">
            <FileTreeNode 
              v-for="node in appendProjectTree" 
              :key="node.path"
              :node="node"
              :selected-files="appendSelectedFilePaths"
              :expanded-folders="appendExpandedFolders"
              @toggle-file="toggleAppendFile"
              @toggle-folder="toggleAppendFolder"
            />
          </div>
        </div>
        
        <div class="modal-actions">
          <button 
            @click="appendFromProject" 
            :disabled="!appendProjectName || appendSelectedFilesCount === 0 || isAiProcessing" 
            class="btn-primary"
          >
            {{ isAiProcessing ? 'Обработка...' : `Добавить проект (${appendSelectedFilesCount} файлов)` }}
          </button>
          <button @click="showAppendFromProject = false" class="btn-secondary">Отмена</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import FileTreeNode from '@/components/FileTreeNode.vue'

const resumes = ref<any[]>([])
const chats = ref<any[]>([])
const userId = ref<number>(1)

const showCreateModal = ref(false)
const createMethod = ref<string | null>(null)
const resumeTitle = ref('')
const selectedFile = ref<File | null>(null)
const selectedSessionId = ref<number | null>(null)
const projectFiles = ref<File[]>([])
const projectTree = ref<any[] | null>(null)
const selectedFilePaths = ref<Set<string>>(new Set())
const expandedFolders = ref<Record<string, boolean>>({ 'root': true })
const viewingResume = ref<any>(null)
const editingResume = ref<any>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)

// Переменные для ИИ-функционала
const isAiProcessing = ref(false)
const showAppendFromChat = ref(false)
const showAppendFromProject = ref(false)
const appendChatSessionId = ref<number | null>(null)
const appendChatType = ref('all')
const appendProjectName = ref('')
const appendProjectFiles = ref<File[]>([])
const appendProjectTree = ref<any[] | null>(null)
const appendSelectedFilePaths = ref<Set<string>>(new Set())
const appendExpandedFolders = ref<Record<string, boolean>>({ 'root': true })
const appendFileInputRef = ref<HTMLInputElement | null>(null)

// Вычисляемое количество выбранных файлов
const selectedFilesCount = computed(() => {
  return selectedFilePaths.value.size
})

// Подсчёт общего количества файлов
const totalFilesCount = computed(() => {
  return projectFiles.value.length
})

// Вычисляемое количество выбранных файлов
const appendSelectedFilesCount = computed(() => {
  return appendSelectedFilePaths.value.size
})

// Подсчёт общего количества файлов
const appendTotalFilesCount = computed(() => {
  return appendProjectFiles.value.length
})

// Загрузка списка резюме
async function loadResumes() {
  try {
    const uid = localStorage.getItem('user_id')
    if (!uid) return
    userId.value = parseInt(uid)
    const response = await fetch(`http://127.0.0.1:8000/api/resumes?user_id=${userId.value}`)
    if (response.ok) resumes.value = await response.json()
  } catch (err) { console.error('Failed to load resumes:', err) }
}

// Загрузка списка чатов
async function loadChats() {
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/chats?user_id=${userId.value}`)
    if (response.ok) chats.value = await response.json()
  } catch (err) { console.error('Failed to load chats:', err) }
}

// Выбор метода создания
function selectCreateMethod(method: string) { 
  createMethod.value = method
  showCreateModal.value = false 
  if (method === 'project') {
    resetProjectSelection()
  }
}

function cancelCreate() { 
  createMethod.value = null
  resumeTitle.value = ''
  selectedFile.value = null
  selectedSessionId.value = null
  resetProjectSelection()
}

function resetProjectSelection() {
  projectFiles.value = []
  projectTree.value = null
  selectedFilePaths.value = new Set()
  expandedFolders.value = { 'root': true }
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

// Обработчики файлов (для создания)
function handleFileUpload(event: Event) { 
  const target = event.target as HTMLInputElement
  if (target.files?.[0]) selectedFile.value = target.files[0] 
}

function handleProjectFolder(event: Event) {
  const target = event.target as HTMLInputElement
  if (!target.files) return

  projectFiles.value = Array.from(target.files)
  projectTree.value = buildFileTree(projectFiles.value)
  
  selectedFilePaths.value = new Set(projectFiles.value.map(f => f.webkitRelativePath))
  expandedFolders.value = { 'root': true }
}

// Построение дерева файлов
function buildFileTree(files: File[]) {
  const root: any = {
    name: 'root',
    path: '',
    isFolder: true,
    children: {},
    level: 0
  }

  files.forEach(file => {
    const parts = file.webkitRelativePath.split('/')
    let current = root

    parts.forEach((part, index) => {
      const isFile = index === parts.length - 1
      const currentPath = parts.slice(0, index + 1).join('/')

      if (!current.children[part]) {
        current.children[part] = {
          name: part,
          path: currentPath,
          isFolder: !isFile,
          children: isFile ? null : {},
          file: isFile ? file : null,
          size: isFile ? file.size : 0,
          level: index
        }
      }

      if (!isFile) {
        current.children[part].size += file.size
      }

      current = current.children[part]
    })
  })

  return convertToTreeArray(root)
}

function convertToTreeArray(node: any) {
  const result: any[] = []

  if (node.children) {
    Object.values(node.children).forEach((child: any) => {
      result.push({
        ...child,
        children: child.isFolder ? convertToTreeArray(child) : null
      })
    })
  }

  return result.sort((a, b) => {
    if (a.isFolder && !b.isFolder) return -1
    if (!a.isFolder && b.isFolder) return 1
    return a.name.localeCompare(b.name)
  })
}

// Управление выбором файлов (для создания)
function toggleFile(path: string) {
  if (selectedFilePaths.value.has(path)) {
    selectedFilePaths.value.delete(path)
  } else {
    selectedFilePaths.value.add(path)
  }
}

function toggleFolder(path: string) {
  expandedFolders.value[path] = !expandedFolders.value[path]
}

function selectAllFiles() {
  projectFiles.value.forEach(f => selectedFilePaths.value.add(f.webkitRelativePath))
}

function deselectAllFiles() {
  selectedFilePaths.value.clear()
}

function selectCodeOnly() {
  const codeExtensions = [
    '.js', '.ts', '.vue', '.py', '.java', '.cpp', '.c', '.cs',
    '.php', '.rb', '.go', '.rs', '.sql', '.html', '.css',
    '.json', '.yaml', '.yml', '.md', '.tsx', '.jsx', '.aspx'
  ]

  selectedFilePaths.value.clear()
  projectFiles.value.forEach(file => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    if (codeExtensions.includes(ext)) {
      selectedFilePaths.value.add(file.webkitRelativePath)
    }
  })
}

function expandAll() {
  const allPaths: Record<string, boolean> = { 'root': true }
  const collectPaths = (nodes: any[]) => {
    nodes.forEach(node => {
      if (node.isFolder) {
        allPaths[node.path] = true
        if (node.children) {
          collectPaths(node.children)
        }
      }
    })
  }
  if (projectTree.value) {
    collectPaths(projectTree.value)
    expandedFolders.value = allPaths
  }
}

function collapseAll() {
  expandedFolders.value = { 'root': true }
}

// Загрузка файла
async function uploadResume() {
  if (!selectedFile.value || !resumeTitle.value) return
  const formData = new FormData()
  formData.append('user_id', userId.value.toString())
  formData.append('title', resumeTitle.value)
  formData.append('file', selectedFile.value)
  try {
    const response = await fetch('http://127.0.0.1:8000/api/resumes/upload', { method: 'POST', body: formData })
    if (response.ok) { await loadResumes(); cancelCreate() }
    else alert('Ошибка загрузки')
  } catch (err) { console.error(err); alert('Ошибка загрузки') }
}

// Создание из чата
async function createResumeFromChat() {
  if (!selectedSessionId.value || !resumeTitle.value) return
  const formData = new FormData()
  formData.append('user_id', userId.value.toString())
  formData.append('session_id', selectedSessionId.value.toString())
  formData.append('title', resumeTitle.value)
  try {
    const response = await fetch('http://127.0.0.1:8000/api/resumes/from-chat', { method: 'POST', body: formData })
    if (response.ok) { await loadResumes(); cancelCreate() }
    else alert('Ошибка создания')
  } catch (err) { console.error(err); alert('Ошибка создания') }
}

// Создание из проекта
async function createResumeFromProject() {
  if (!projectFiles.value.length || !resumeTitle.value || selectedFilesCount.value === 0) return

  const filesToUpload = projectFiles.value.filter(f => selectedFilePaths.value.has(f.webkitRelativePath))

  if (filesToUpload.length === 0) {
    alert('Выберите хотя бы один файл')
    return
  }

  const formData = new FormData()
  formData.append('user_id', userId.value.toString())
  formData.append('title', resumeTitle.value)

  filesToUpload.forEach(file => formData.append('project_files', file))

  try {
    const response = await fetch('http://127.0.0.1:8000/api/resumes/from-project', { 
      method: 'POST', 
      body: formData 
    })
    if (response.ok) { 
      await loadResumes()
      cancelCreate() 
    } else {
      const error = await response.json()
      alert(`Ошибка: ${error.detail || 'Не удалось создать резюме'}`)
    }
  } catch (err) { 
    console.error(err)
    alert('Ошибка создания') 
  }
}

// Просмотр и редактирование
async function viewResume(resumeId: number) {
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/resumes/${resumeId}?user_id=${userId.value}`)
    if (response.ok) { viewingResume.value = await response.json(); editingResume.value = null }
  } catch (err) { console.error(err) }
}

function editResume(resumeId: number) {
  viewResume(resumeId)
  setTimeout(() => { if (viewingResume.value) { editingResume.value = { ...viewingResume.value }; viewingResume.value = null } }, 100)
}

function closeEditor() { viewingResume.value = null; editingResume.value = null }

async function saveResume() {
  if (!editingResume.value) return
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/resumes/${editingResume.value.resume_id}?user_id=${userId.value}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: editingResume.value.title,
        content: editingResume.value.content,
        status: editingResume.value.status
      })
    })
    if (response.ok) { await loadResumes(); closeEditor() }
    else alert('Ошибка сохранения')
  } catch (err) { console.error(err); alert('Ошибка сохранения') }
}

async function improveResume(improvementType: string) {
  if (!editingResume.value) return
  
  isAiProcessing.value = true
  
  try {
    const formData = new FormData()
    formData.append('user_id', userId.value.toString())
    formData.append('improvement_type', improvementType)
    
    const response = await fetch(`http://127.0.0.1:8000/api/resumes/${editingResume.value.resume_id}/improve`, {
      method: 'POST',
      body: formData
    })
    
    if (response.ok) {
      const updatedResume = await fetch(
        `http://127.0.0.1:8000/api/resumes/${editingResume.value.resume_id}?user_id=${userId.value}`
      )
      if (updatedResume.ok) {
        const data = await updatedResume.json()
        editingResume.value.content = data.content
      }
    } else {
      const error = await response.json()
      alert(`Ошибка: ${error.detail || 'Не удалось улучшить резюме'}`)
    }
  } catch (err) {
    console.error('Improve error:', err)
    alert('❌ Ошибка при улучшении резюме')
  } finally {
    isAiProcessing.value = false
  }
}

// Дополнение из чата
async function appendFromChat() {
  if (!editingResume.value || !appendChatSessionId.value) return
  
  isAiProcessing.value = true
  
  try {
    const formData = new FormData()
    formData.append('user_id', userId.value.toString())
    formData.append('session_id', appendChatSessionId.value.toString())
    formData.append('append_type', appendChatType.value)
    
    const response = await fetch(`http://127.0.0.1:8000/api/resumes/${editingResume.value.resume_id}/append-from-chat`, {
      method: 'POST',
      body: formData
    })
    
    if (response.ok) {
      const updatedResume = await fetch(
        `http://127.0.0.1:8000/api/resumes/${editingResume.value.resume_id}?user_id=${userId.value}`
      )
      if (updatedResume.ok) {
        const data = await updatedResume.json()
        editingResume.value.content = data.content
      }
      showAppendFromChat.value = false
    } else {
      const error = await response.json()
      alert(`Ошибка: ${error.detail || 'Не удалось дополнить резюме'}`)
    }
  } catch (err) {
    console.error('Append chat error:', err)
    alert('❌ Ошибка при дополнении')
  } finally {
    isAiProcessing.value = false
  }
}

// Обработка выбора папки для дополнения
function handleAppendProjectFolder(event: Event) {
  const target = event.target as HTMLInputElement
  if (!target.files) return

  appendProjectFiles.value = Array.from(target.files)
  appendProjectTree.value = buildFileTree(appendProjectFiles.value)
  
  appendSelectedFilePaths.value = new Set(appendProjectFiles.value.map(f => f.webkitRelativePath))
  appendExpandedFolders.value = { 'root': true }
}

// Управление выбором файлов для дополнения
function toggleAppendFile(path: string) {
  if (appendSelectedFilePaths.value.has(path)) {
    appendSelectedFilePaths.value.delete(path)
  } else {
    appendSelectedFilePaths.value.add(path)
  }
}

function toggleAppendFolder(path: string) {
  appendExpandedFolders.value[path] = !appendExpandedFolders.value[path]
}

function appendSelectAllFiles() {
  appendProjectFiles.value.forEach(f => appendSelectedFilePaths.value.add(f.webkitRelativePath))
}

function appendDeselectAllFiles() {
  appendSelectedFilePaths.value.clear()
}

function appendSelectCodeOnly() {
  const codeExtensions = [
    '.js', '.ts', '.vue', '.py', '.java', '.cpp', '.c', '.cs',
    '.php', '.rb', '.go', '.rs', '.sql', '.html', '.css',
    '.json', '.yaml', '.yml', '.md', '.tsx', '.jsx', '.aspx'
  ]
  
  appendSelectedFilePaths.value.clear()
  appendProjectFiles.value.forEach(file => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    if (codeExtensions.includes(ext)) {
      appendSelectedFilePaths.value.add(file.webkitRelativePath)
    }
  })
}

// Дополнение из проекта
async function appendFromProject() {
  if (!editingResume.value || !appendProjectFiles.value.length || !appendProjectName.value || appendSelectedFilesCount.value === 0) return
  
  isAiProcessing.value = true
  
  try {
    const filesToUpload = appendProjectFiles.value.filter(f => appendSelectedFilePaths.value.has(f.webkitRelativePath))
    
    const formData = new FormData()
    formData.append('user_id', userId.value.toString())
    formData.append('project_name', appendProjectName.value)
    
    filesToUpload.forEach(file => {
      formData.append('project_files', file)
    })
    
    const response = await fetch(`http://127.0.0.1:8000/api/resumes/${editingResume.value.resume_id}/append-from-project`, {
      method: 'POST',
      body: formData
    })
    
    if (response.ok) {
      const updatedResume = await fetch(
        `http://127.0.0.1:8000/api/resumes/${editingResume.value.resume_id}?user_id=${userId.value}`
      )
      if (updatedResume.ok) {
        const data = await updatedResume.json()
        editingResume.value.content = data.content
      }
      showAppendFromProject.value = false
      
      appendProjectFiles.value = []
      appendProjectTree.value = null
      appendSelectedFilePaths.value = new Set()
      appendExpandedFolders.value = { 'root': true }
      appendProjectName.value = ''
      if (appendFileInputRef.value) {
        appendFileInputRef.value.value = ''
      }
    } else {
      const error = await response.json()
      alert(`Ошибка: ${error.detail || 'Не удалось добавить проект'}`)
    }
  } catch (err) {
    console.error('Append project error:', err)
    alert('❌ Ошибка при добавлении проекта')
  } finally {
    isAiProcessing.value = false
  }
}

async function setPrimary(resumeId: number) {
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/resumes/${resumeId}?user_id=${userId.value}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_primary: true })
    })
    if (response.ok) await loadResumes()
  } catch (err) { console.error(err) }
}

async function deleteResume(resumeId: number) {
  if (!confirm('Удалить это резюме?')) return
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/resumes/${resumeId}?user_id=${userId.value}`, { method: 'DELETE' })
    if (response.ok) await loadResumes()
  } catch (err) { console.error(err) }
}

// Утилиты
function formatDate(dateStr: string) { return new Date(dateStr).toLocaleDateString('ru-RU') }
function formatResumeContent(content: string) {
  return content.replace(/^### (.*$)/gim, '<h3>$1</h3>').replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>').replace(/\*\*(.*)\*\*/gim, '<b>$1</b>')
    .replace(/\*(.*)\*/gim, '<i>$1</i>').replace(/\n/gim, '<br>')
}

onMounted(() => { loadResumes(); loadChats() })
</script>

<style scoped>
.resume-page { 
  padding: 32px 24px; 
  max-width: 1200px; 
  margin: 0 auto; 
}
.resume-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  margin-bottom: 32px; 
}
.btn-create { 
  padding: 12px 24px; 
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
  color: white; 
  border: none; 
  border-radius: 8px; 
  font-weight: 600; 
  cursor: pointer; 
}
.resumes-list { 
  display: grid; 
  gap: 16px; 
}
.resume-card { 
  background: white; 
  padding: 24px; 
  border-radius: 12px; 
  box-shadow: 0 2px 8px rgba(0,0,0,0.1); 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  border-left: 4px solid #e2e8f0; 
}
.resume-card.primary { 
  border-left-color: #667eea; 
  background: #f7fafc; 
}
.resume-info h3 { 
  margin: 0 0 8px 0; 
  color: #2d3748; 
}
.resume-meta { 
  display: flex; 
  gap: 12px; 
  align-items: center; 
  flex-wrap: wrap; 
}
.status { 
  padding: 4px 12px; 
  border-radius: 12px; 
  font-size: 0.85rem; 
  font-weight: 500; 
}
.status.draft { 
  background: #fed7d7; 
  color: #c53030; 
}
.status.published { 
  background: #c6f6d5; 
  color: #22543d; 
}
.primary-badge { 
  padding: 4px 12px; 
  background: #667eea; 
  color: white; 
  border-radius: 12px; 
  font-size: 0.85rem; 
  font-weight: 500; 
}
.date { 
  color: #718096; 
  font-size: 0.9rem; 
}
.resume-actions { 
  display: flex; 
  gap: 8px; 
}
.btn-action { 
  padding: 8px 16px; 
  background: #e2e8f0; 
  border: none; 
  border-radius: 6px; 
  cursor: pointer; 
  font-weight: 500; 
}
.btn-action.delete { 
  background: #fed7d7; 
  color: #c53030; 
}
.empty-state { 
  text-align: center; 
  padding: 80px 20px; 
  color: #718096; 
}
.modal-overlay { 
  position: fixed; 
  top: 0; 
  left: 0; 
  right: 0; 
  bottom: 0; 
  background: rgba(0,0,0,0.5); 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  z-index: 1000; }
.modal { 
  background: white; 
  padding: 32px; 
  border-radius: 16px; 
  max-width: 500px; 
  width: 90%; 
  max-height: 90vh; 
  overflow-y: auto; }
.modal.large { 
  max-width: 900px; 
}
.modal.extra-large { 
  max-width: 1100px; 
}
.create-options { 
  display: grid; 
  grid-template-columns: repeat(3, 1fr); 
  gap: 16px; 
  margin: 24px 0; 
}
.option-card { 
  padding: 24px; 
  background: #f7fafc; 
  border: 2px solid #e2e8f0; 
  border-radius: 12px; 
  cursor: pointer; 
  text-align: center; 
  transition: all 0.2s; 
}
.option-card:hover { 
  border-color: #667eea; 
  background: #edf2f7; 
  transform: translateY(-2px); 
}
.option-icon { 
  font-size: 3rem; 
  margin-bottom: 12px; }
.option-card h3 { 
  margin: 0 0 8px 0; 
  color: #2d3748; }
.option-card p { 
  margin: 0; 
  color: #718096; 
  font-size: 0.9rem; }
.form-group { 
  margin-bottom: 20px; 
}
.form-group label { 
  display: block; 
  margin-bottom: 8px; 
  font-weight: 600; 
  color: #4a5568; }
.form-group input, .form-group select { 
  width: 100%; 
  padding: 12px; 
  border: 2px solid #e2e8f0; 
  border-radius: 8px; 
  font-size: 1rem; 
}
.hint { 
  margin-top: 8px; 
  color: #718096; 
  font-size: 0.85rem; 
}
.modal-actions { 
  display: flex; 
  gap: 12px; 
  justify-content: flex-end; 
  margin-top: 24px; 
}
.btn-primary { 
  padding: 12px 24px; 
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
  color: white; 
  border: none; 
  border-radius: 8px; 
  font-weight: 600; 
  cursor: pointer; 
}
.btn-primary:disabled { 
  opacity: 0.5; 
  cursor: not-allowed; 
}
.btn-secondary { 
  padding: 12px 24px; 
  background: #e2e8f0; 
  border: none; 
  border-radius: 8px; 
  font-weight: 600; 
  cursor: pointer; 
}
.btn-cancel { 
  margin-top: 24px; 
  padding: 12px 24px; 
  background: #e2e8f0; 
  border: none; 
  border-radius: 8px; 
  font-weight: 600; 
  cursor: pointer; 
  width: 100%; 
}
.resume-content, .edit-content { 
  background: #f7fafc; 
  padding: 24px; 
  border-radius: 8px; 
  margin: 24px 0; 
  line-height: 1.6; 
}
.edit-title { 
  width: 100%; 
  padding: 12px; 
  margin-bottom: 16px; 
  border: 2px solid #e2e8f0; 
  border-radius: 8px; 
  font-size: 1.1rem; 
}
.edit-content { 
  width: 100%; 
  font-family: monospace; 
  font-size: 0.95rem; 
}
.editor-controls { 
  display: flex; 
  flex-direction: column; 
  gap: 16px; 
}
.form-row { 
  display: flex; 
  align-items: center; 
  gap: 12px; 
  margin-bottom: 12px; 
}
.form-row label { 
  font-weight: 600; 
  color: #4a5568; 
}
.edit-select { 
  padding: 8px 12px; 
  border: 2px solid #e2e8f0; 
  border-radius: 6px; 
  font-size: 1rem; 
}
.folder-input {
  padding: 12px;
  border: 2px dashed #cbd5e0;
  border-radius: 8px;
  width: 100%;
  cursor: pointer;
  margin-bottom: 16px;
}

.file-tree-container {
  margin-top: 20px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
  max-height: 500px;
  display: flex;
  flex-direction: column;
}

.file-tree-container h3 {
  margin: 0 0 12px 0;
  font-size: 1rem;
  color: #4a5568;
}

.tree-controls {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e2e8f0;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 0.85rem;
  border: 1px solid #cbd5e0;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-sm:hover {
  background: #f7fafc;
  border-color: #667eea;
}

.tree-scroll {
  overflow-y: auto;
  max-height: 400px;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  padding: 12px;
  background: #f7fafc;
}

.ai-improvement-panel {
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 24px;
  border: 2px solid #cbd5e0;
}

.ai-improvement-panel h3 {
  margin: 0 0 16px 0;
  color: #4a5568;
  font-size: 1.1rem;
}

.improvement-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.btn-ai {
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.btn-ai:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-ai:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.append-section {
  border-top: 1px solid #cbd5e0;
  padding-top: 16px;
  margin-top: 16px;
}

.append-section h4 {
  margin: 0 0 12px 0;
  color: #4a5568;
  font-size: 1rem;
}

.append-buttons {
  display: flex;
  gap: 12px;
}

.btn-append {
  padding: 10px 20px;
  background: white;
  border: 2px solid #667eea;
  color: #667eea;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-append:hover {
  background: #667eea;
  color: white;
}

.ai-processing {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  margin-top: 16px;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #e2e8f0;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.ai-processing p {
  margin: 0;
  color: #4a5568;
  font-weight: 500;
}
</style>