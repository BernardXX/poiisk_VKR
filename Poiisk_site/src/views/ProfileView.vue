<template>
  <div class="profile-page">
    <h1>👤 Настройка профиля</h1>
    
    <!-- Табы -->
    <div class="tabs">
      <button :class="{ active: activeTab === 'profile' }" @click="activeTab = 'profile'">📝 Профиль</button>
      <button :class="{ active: activeTab === 'security' }" @click="activeTab = 'security'">🔒 Безопасность</button>
    </div>

    <!-- Вкладка профиль -->
    <form v-if="activeTab === 'profile'" @submit.prevent="saveProfile" class="profile-form">
      <section class="form-section">
        <h2>📝 Личная информация</h2>
        <div class="input-row">
          <div class="input-group">
            <label>ФИО</label>
            <input v-model="form.fullName" placeholder="Иванов Иван Иванович" />
          </div>
          <div class="input-group">
            <label>Телефон</label>
            <input v-model="form.phone" placeholder="+7 (999) 123-45-67" />
          </div>
        </div>
      </section>

      <section class="form-section">
        <h2>💼 Карьерные предпочтения</h2>
        <div class="input-row">
          <div class="input-group">
            <label>Желаемая роль</label>
            <input v-model="form.desiredRole" placeholder="Frontend Developer" />
          </div>
          <div class="input-group">
            <label>Город / Формат</label>
            <input v-model="form.location" placeholder="Москва / Удалённо" />
          </div>
          <div class="input-group">
            <label>Уровень</label>
            <select v-model="form.level">
              <option value="">Выберите уровень</option>
              <option value="Junior">Junior</option>
              <option value="Middle">Middle</option>
              <option value="Senior">Senior</option>
              <option value="Lead">Lead</option>
            </select>
          </div>
        </div>
      </section>

      <section class="form-section">
        <h2>🔗 Ссылки</h2>
        <div v-for="(link, index) in socialLinksArray" :key="link.id" class="dynamic-row">
          <input v-model="link.name" placeholder="GitHub, Telegram..." class="flex-2" />
          <input v-model="link.url" placeholder="https://..." class="flex-3" />
          <button type="button" @click="removeLink(index)" class="btn-icon remove">−</button>
        </div>
        <button type="button" @click="addLink" class="btn-add">+ Добавить ссылку</button>
      </section>

      <section class="form-section">
        <div class="section-header" @click="skillsSectionExpanded = !skillsSectionExpanded">
          <h2>🛠 Навыки</h2>
          <button type="button" class="btn-toggle" :class="{ collapsed: !skillsSectionExpanded }">
            {{ skillsSectionExpanded ? 'Свернуть' : 'Развернуть' }}
          </button>
        </div>

        <div v-if="skillsSectionExpanded" class="section-content">

            <!-- Кнопка импорта -->
            <button type="button" @click="openImportModal" class="btn-import-skills">
              📥 Загрузить из резюме
            </button>

            <div v-for="(skill, index) in skillsArray" :key="skill.id" class="dynamic-row">
              <input v-model="skill.name" placeholder="Python, Vue.js..." class="flex-2" />
              <label class="priority-toggle">
                <input type="checkbox" v-model="skill.isPriority" />
                <span>⭐ Приоритетный</span>
              </label>
              <button type="button" @click="removeSkill(index)" class="btn-icon remove">−</button>
            </div>
            <button type="button" @click="addSkill" class="btn-add">+ Добавить навык</button>
        </div>
      </section>

      <!-- Сообщение об успехе/ошибке для профиля -->
      <p v-if="profileError" class="error-message">{{ profileError }}</p>
      <p v-if="profileSuccess" class="success-message">{{ profileSuccess }}</p>

      <button type="submit" :disabled="isLoading" class="btn-save">
        {{ isLoading ? 'Сохранение...' : '💾 Сохранить профиль' }}
      </button>
    </form>

    <!-- Вкладка: Безопасность -->
    <div v-if="activeTab === 'security'" class="security-form">
      <section class="form-section">
        <h2>📧 Смена Email</h2>
        <div class="input-group">
          <label>Новый Email</label>
          <input v-model="security.newEmail" type="email" placeholder="new@email.com" />
        </div>
        <div class="input-group">
          <label>Текущий пароль (для подтверждения)</label>
          <input v-model="security.currentPassEmail" type="password" placeholder="••••••••" />
        </div>
        
        <!-- Сообщения для email -->
        <p v-if="emailError" class="error-message">{{ emailError }}</p>
        <p v-if="emailSuccess" class="success-message">{{ emailSuccess }}</p>
        
        <button @click="changeEmail" :disabled="secLoading" class="btn-action">
          {{ secLoading ? 'Обновление...' : 'Обновить Email' }}
        </button>
      </section>

      <section class="form-section">
        <h2>🔑 Смена Пароля</h2>
        <div class="input-group">
          <label>Текущий пароль</label>
          <input v-model="security.currentPass" type="password" placeholder="••••••••" />
        </div>
        <div class="input-group">
          <label>Новый пароль</label>
          <input v-model="security.newPass" type="password" minlength="6" placeholder="Минимум 6 символов" />
        </div>
        
        <!-- Сообщения для пароля -->
        <p v-if="passwordError" class="error-message">{{ passwordError }}</p>
        <p v-if="passwordSuccess" class="success-message">{{ passwordSuccess }}</p>
        
        <button @click="changePassword" :disabled="secLoading" class="btn-action">
          {{ secLoading ? 'Обновление...' : 'Сменить пароль' }}
        </button>
      </section>
    </div>

    <!-- МОДАЛЬНОЕ ОКНО: Выбор резюме для импорта навыков (ПОВЕРХ СТРАНИЦЫ) -->
    <div v-if="showImportModal" class="modal-overlay" @click.self="showImportModal = false">
      <div class="modal">
        <h2>📥 Загрузить навыки из резюме</h2>
        <p class="hint">Выберите резюме, из которого нужно извлечь навыки</p>
        
        <div v-if="importLoading" class="loading-state">
          <div class="spinner"></div>
          <p>Анализируем резюме...</p>
        </div>
        
        <div v-else-if="availableResumes.length > 0" class="resumes-grid">
          <div 
            v-for="resume in availableResumes" 
            :key="resume.resume_id"
            @click="importSkills(resume.resume_id)"
            class="resume-card-import"
            :class="{ primary: resume.is_primary }"
          >
            <div class="resume-card-header">
              <h3>{{ resume.title }}</h3>
              <span class="status" :class="resume.status">
                {{ resume.status === 'draft' ? 'Черновик' : 'Готовое' }}
              </span>
            </div>
            <div class="resume-card-footer">
              <span v-if="resume.is_primary" class="primary-badge">⭐ Основное</span>
              <span class="date">Обновлено: {{ formatDate(resume.updated_at) }}</span>
            </div>
          </div>
        </div>
        
        <div v-else class="empty-state-modal">
          <p>У вас пока нет резюме</p>
          <button @click="showImportModal = false; $router.push('/resume')" class="btn-primary-small">
            + Создать резюме
          </button>
        </div>

        <button @click="showImportModal = false" class="btn-cancel">Отмена</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'

const isLoading = ref(false)
const secLoading = ref(false)
const activeTab = ref('profile')
const userId = ref<number>(1)

// Сообщения об ошибках и успехе
const profileError = ref('')
const profileSuccess = ref('')
const emailError = ref('')
const emailSuccess = ref('')
const passwordError = ref('')
const passwordSuccess = ref('')

const showImportModal = ref(false)
const availableResumes = ref<any[]>([])
const importLoading = ref(false)

const skillsSectionExpanded = ref(true)  // По умолчанию развёрнуто

const form = reactive({
  fullName: '',
  phone: '',
  desiredRole: '',
  location: '',
  level: ''
})

const security = reactive({
  newEmail: '',
  currentPassEmail: '',
  currentPass: '',
  newPass: ''
})

const socialLinksArray = ref<{ id: number; name: string; url: string }[]>([])
const skillsArray = ref<{ id: number; name: string; isPriority: boolean }[]>([])
let nextId = 1

// Функция для очистки сообщений
function clearMessages() {
  profileError.value = ''
  profileSuccess.value = ''
  emailError.value = ''
  emailSuccess.value = ''
  passwordError.value = ''
  passwordSuccess.value = ''
}

async function loadProfile() {
  try {
    const uid = localStorage.getItem('user_id')
    if (!uid) return
    userId.value = parseInt(uid)

    const res = await fetch(`http://127.0.0.1:8000/api/profile/?user_id=${userId.value}`)
    if (!res.ok) return
    const data = await res.json()

    form.fullName = data.full_name || ''
    form.phone = data.phone || ''
    form.desiredRole = data.desired_role || ''
    form.location = data.location || ''
    form.level = data.level || ''

    socialLinksArray.value = Object.entries(data.social_links || {}).map(([n, u]) => ({
      id: nextId++,
      name: n,
      url: u as string
    }))

    skillsArray.value = Object.entries(data.skills || {}).map(([n, v]) => ({
      id: nextId++,
      name: n,
      isPriority: typeof v === 'object' ? v.is_priority : false
    }))
  } catch (err) {
    console.error('Failed to load profile:', err)
  }
}

function addLink() {
  socialLinksArray.value.push({ id: nextId++, name: '', url: '' })
}
function removeLink(index: number) {
  socialLinksArray.value.splice(index, 1)
}
function addSkill() {
  skillsArray.value.push({ id: nextId++, name: '', isPriority: false })
}
function removeSkill(index: number) {
  skillsArray.value.splice(index, 1)
}

async function saveProfile() {
  clearMessages()
  isLoading.value = true

  try {
    const sObj: Record<string, string> = {}
    socialLinksArray.value.forEach(l => {
      if (l.name && l.url) sObj[l.name] = l.url
    })

    const skObj: Record<string, { is_priority: boolean }> = {}
    skillsArray.value.forEach(s => {
      if (s.name) skObj[s.name] = { is_priority: s.isPriority }
    })

    const res = await fetch(`http://127.0.0.1:8000/api/profile/?user_id=${userId.value}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        full_name: form.fullName,
        phone: form.phone,
        social_links: sObj,
        desired_role: form.desiredRole,
        location: form.location,
        level: form.level,
        skills: skObj
      })
    })

    if (res.ok) {
      profileSuccess.value = '✅ Профиль успешно сохранён!'
      await loadProfile()
      // Очищаем успех через 3 секунды
      setTimeout(() => { profileSuccess.value = '' }, 3000)
    } else {
      const errorData = await res.json()
      profileError.value = errorData.detail || '❌ Ошибка при сохранении профиля'
    }
  } catch (err) {
    console.error('Save error:', err)
    profileError.value = '❌ Ошибка соединения с сервером'
  } finally {
    isLoading.value = false
  }
}

async function changeEmail() {
  clearMessages()

  if (!security.newEmail || !security.currentPassEmail) {
    emailError.value = '⚠️ Заполните все поля'
    return
  }

  secLoading.value = true

  try {
    const res = await fetch(`http://127.0.0.1:8000/auth/change-email?user_id=${userId.value}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        new_email: security.newEmail,
        current_password: security.currentPassEmail
      })
    })

    if (res.ok) {
      const data = await res.json()
      emailSuccess.value = data.message || '✅ Email успешно изменён'
      localStorage.setItem('user_email', security.newEmail)
      security.newEmail = ''
      security.currentPassEmail = ''
      setTimeout(() => { emailSuccess.value = '' }, 3000)
    } else {
      const errorData = await res.json()

      // Перевод ошибок валидации на русский
      if (res.status === 422) {
        const errors = Array.isArray(errorData) ? errorData : (errorData.detail || [])

        if (errors.length > 0) {
          const emailErr = errors.find((e: any) => e.loc?.includes('new_email'))
          const errorMsg = emailErr?.msg || errors[0].msg || ''

          // Перевод стандартных сообщений Pydantic
          if (errorMsg.includes('value is not a valid email address')) {
            if (errorMsg.includes('period immediately after the @-sign')) {
              emailError.value = '❌ Неверный формат email: точка не может стоять сразу после знака @'
            } else if (errorMsg.includes('period at the end')) {
              emailError.value = '❌ Неверный формат email: email не может заканчиваться на точку'
            } else {
              emailError.value = '❌ Неверный формат email адреса'
            }
          } else if (errorMsg.includes('not a valid email')) {
            emailError.value = '❌ Введите корректный email адрес (например: name@example.com)'
          } else {
            emailError.value = `❌ ${errorMsg}`
          }
        } else {
          emailError.value = '❌ Ошибка валидации данных'
        }
      } else if (res.status === 401) {
        emailError.value = typeof errorData.detail === 'string' ? errorData.detail : '❌ Неверный текущий пароль'
      } else if (res.status === 400) {
        emailError.value = typeof errorData.detail === 'string' ? errorData.detail : '❌ Этот email уже занят'
      } else {
        emailError.value = typeof errorData.detail === 'string' ? errorData.detail : `❌ Ошибка сервера (${res.status})`
      }
    }
  } catch (err) {
    console.error('Email change error:', err)
    emailError.value = '❌ Ошибка соединения с сервером'
  } finally {
    secLoading.value = false
  }
}

async function changePassword() {
  clearMessages()

  if (!security.currentPass || !security.newPass) {
    passwordError.value = '⚠️ Заполните все поля'
    return
  }

  if (security.newPass.length < 6) {
    passwordError.value = '⚠️ Новый пароль должен быть не менее 6 символов'
    return
  }

  secLoading.value = true

  try {
    const res = await fetch(`http://127.0.0.1:8000/auth/change-password?user_id=${userId.value}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        current_password: security.currentPass,
        new_password: security.newPass
      })
    })

    const data = await res.json()

    if (res.ok) {
      passwordSuccess.value = data.message || '✅ Пароль успешно изменён'
      security.currentPass = ''
      security.newPass = ''
      // Очищаем успех через 3 секунды
      setTimeout(() => { passwordSuccess.value = '' }, 3000)
    } else {
      // Правильное извлечение ошибки как в Register.vue
      if (res.status === 401) {
        passwordError.value = data.detail || '❌ Неверный текущий пароль'
      } else {
        passwordError.value = data.detail || `❌ Ошибка ${res.status}`
      }
    }
  } catch (err) {
    console.error('Password change error:', err)
    passwordError.value = '❌ Ошибка соединения с сервером'
  } finally {
    secLoading.value = false
  }
}

// Функция открытия модалки и загрузки списка резюме
async function openImportModal() {
  showImportModal.value = true
  availableResumes.value = []
  importLoading.value = false

  const uid = localStorage.getItem('user_id')
  if (!uid) return

  try {
    // Загружаем список резюме пользователя
    const res = await fetch(`http://127.0.0.1:8000/api/resumes?user_id=${uid}`)
    if (res.ok) {
      availableResumes.value = await res.json()
    }
  } catch (err) {
    console.error("Не удалось загрузить список резюме", err)
  }
}

// Функция импорта навыков из выбранного резюме
async function importSkills(resumeId: number) {
  importLoading.value = true
  const uid = localStorage.getItem('user_id')
  if (!uid) return

  try {
    // Вызываем новый эндпоинт бэкенда
    const res = await fetch(`http://127.0.0.1:8000/api/resumes/${resumeId}/skills?user_id=${uid}`)

    if (res.ok) {
      const newSkills = await res.json()

      // Добавляем новые навыки, избегая дубликатов
      newSkills.forEach((skillName: string) => {
        // Проверяем, нет ли уже такого навыка (без учета регистра)
        const exists = skillsArray.value.some(s => s.name.toLowerCase() === skillName.toLowerCase())

        if (!exists && skillName.trim()) {
          skillsArray.value.push({
            id: nextId++,
            name: skillName,
            isPriority: false
          })
        }
      })

      showImportModal.value = false
      // alert('✅ Навыки успешно добавлены!')
    } else {
      alert('❌ Ошибка при анализе резюме')
    }
  } catch (err) {
    console.error(err)
    alert('❌ Ошибка сети')
  } finally {
    importLoading.value = false
  }
}

// Утилиты
function formatDate(dateStr: string) { 
  return new Date(dateStr).toLocaleDateString('ru-RU') 
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.profile-page {
  padding: 32px 24px;
  max-width: 900px;
  margin: 0 auto;
}

h1 {
  margin-bottom: 24px;
  color: #2d3748;
  font-size: 1.8rem;
}

.tabs {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.tabs button {
  padding: 10px 20px;
  background: #e2e8f0;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.tabs button.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.profile-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-section {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.form-section h2 {
  margin: 0 0 16px 0;
  color: #4a5568;
  font-size: 1.2rem;
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 8px;
}

.input-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.input-group label {
  font-weight: 600;
  color: #4a5568;
  font-size: 0.9rem;
}

input, select {
  padding: 10px 14px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

input:focus, select:focus {
  outline: none;
  border-color: #667eea;
}

.dynamic-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.flex-2 { flex: 2; }
.flex-3 { flex: 3; }

.btn-icon {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 8px;
  font-size: 1.2rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.btn-icon.remove {
  background: #fed7d7;
  color: #c53030;
}

.btn-icon.remove:hover {
  background: #e53e3e;
  color: white;
}

.btn-add {
  background: #e2e8f0;
  border: none;
  padding: 10px 16px;
  border-radius: 8px;
  font-weight: 600;
  color: #4a5568;
  cursor: pointer;
  width: 100%;
  margin-top: 8px;
  transition: background 0.2s;
}

.btn-add:hover {
  background: #cbd5e0;
}

.priority-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  user-select: none;
  font-size: 0.95rem;
  color: #4a5568;
  background: #f7fafc;
  padding: 8px 12px;
  border-radius: 8px;
  border: 2px solid #e2e8f0;
  transition: all 0.2s;
}

.priority-toggle:hover {
  border-color: #667eea;
}

.priority-toggle input {
  width: 16px;
  height: 16px;
  accent-color: #667eea;
}

.btn-save {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 14px;
  border-radius: 10px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, opacity 0.2s;
}

.btn-save:hover:not(:disabled) {
  transform: translateY(-2px);
}

.btn-save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.security-form {
  display: grid;
  gap: 24px;
  max-width: 600px;
}

.btn-action {
  margin-top: 12px;
  padding: 10px 20px;
  background: #4a5568;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.2s;
}

.btn-action:hover:not(:disabled) {
  background: #2d3748;
}

.btn-action:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  color: #e53e3e;
  background: #fed7d7;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 0.9rem;
  margin: 12px 0;
  border-left: 4px solid #e53e3e;
}

.success-message {
  color: #22543d;
  background: #c6f6d5;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 0.9rem;
  margin: 12px 0;
  border-left: 4px solid #38a169;
}

.btn-import-skills {
  width: 100%;
  padding: 10px;
  background: #ebf8ff;
  border: 2px solid #bee3f8;
  color: #2b6cb0;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  margin-bottom: 12px;
  transition: all 0.2s;
}

.btn-import-skills:hover {
  background: #bee3f8;
  border-color: #90cdf4;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  padding: 32px;
  border-radius: 16px;
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal h2 {
  margin: 0 0 8px 0;
  color: #2d3748;
}

.modal .hint {
  color: #718096;
  margin-bottom: 24px;
}

.resumes-grid {
  display: grid;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
  margin-bottom: 16px;
}

.resume-card-import {
  background: white;
  padding: 16px;
  border-radius: 10px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  border-left: 4px solid #e2e8f0;
  cursor: pointer;
  transition: all 0.2s;
}

.resume-card-import:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
  border-left-color: #667eea;
}

.resume-card-import.primary {
  border-left-color: #667eea;
  background: #f7fafc;
}

.resume-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.resume-card-header h3 {
  margin: 0;
  color: #2d3748;
  font-size: 1rem;
}

.status {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.status.draft {
  background: #fed7d7;
  color: #c53030;
}

.status.published {
  background: #c6f6d5;
  color: #22543d;
}

.resume-card-footer {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.primary-badge {
  padding: 4px 10px;
  background: #667eea;
  color: white;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.date {
  color: #718096;
  font-size: 0.8rem;
}

.empty-state-modal {
  text-align: center;
  padding: 40px 20px;
  color: #718096;
}

.btn-primary-small {
  margin-top: 16px;
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.9rem;
}

.btn-primary-small:hover {
  transform: translateY(-2px);
}

.loading-state {
  text-align: center;
  padding: 40px 20px;
  color: #4a5568;
}

.loading-state .spinner {
  margin: 0 auto 16px;
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

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e2e8f0;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

.section-header h2 {
  margin: 0;
  color: #4a5568;
  font-size: 1.2rem;
}

.btn-toggle {
  padding: 8px 16px;       
  border: none;
  background: #e2e8f0;
  border-radius: 8px;
  font-size: 0.9rem;         
  font-weight: 600;
  color: #4a5568;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;       
  flex-shrink: 0;        
}

.btn-toggle:hover {
  background: #cbd5e0;
  transform: translateY(-1px);
}

.btn-toggle.collapsed {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3);
}

.section-content {
  margin-top: 16px;
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.resume-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f7fafc;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 10px;
}

.resume-option:hover {
  border-color: #667eea;
  background: #edf2f7;
  transform: translateX(4px);
}

.resume-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: left;
}

.resume-title {
  font-weight: 600;
  color: #2d3748;
  font-size: 1rem;
}

.resume-date {
  font-size: 0.85rem;
  color: #718096;
}

.resume-status {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}

.resume-status.draft {
  background: #fed7d7;
  color: #c53030;
}

.resume-status.published {
  background: #c6f6d5;
  color: #22543d;
}

.empty-state-modal {
  text-align: center;
  padding: 32px 20px;
  color: #718096;
}

.btn-primary-small {
  margin-top: 16px;
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.9rem;
}

.btn-primary-small:hover {
  transform: translateY(-2px);
}

.loading-state {
  text-align: center;
  padding: 40px 20px;
  color: #4a5568;
}

.loading-state .spinner {
  margin: 0 auto 16px;
}
</style>