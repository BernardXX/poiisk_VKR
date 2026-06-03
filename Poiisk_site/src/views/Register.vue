<template>
  <div class="auth-container">
    <div class="auth-card">
      <div class="auth-header">
        <img src="@/assets/poiisk.png" alt="ПоИИск" class="auth-logo-icon" />
      </div>
      <h2 class="auth-subtitle">Регистрация</h2>

      <form @submit.prevent="handleRegister" class="auth-form">
        <div class="form-group">
          <label for="email">Email</label>
          <input
            id="email"
            v-model="email"
            type="email"
            placeholder="your@email.com"
            required
            autocomplete="email"
          />
        </div>

        <div class="form-group">
          <label for="password">Пароль</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="••••••••"
            required
            autocomplete="new-password"
            minlength="6"
          />
        </div>

        <div class="form-group">
          <label for="confirmPassword">Подтвердите пароль</label>
          <input
            id="confirmPassword"
            v-model="confirmPassword"
            type="password"
            placeholder="••••••••"
            required
            autocomplete="new-password"
          />
        </div>

        <button type="submit" class="btn-primary" :disabled="isLoading">
          {{ isLoading ? 'Регистрация...' : 'Зарегистрироваться' }}
        </button>

        <p v-if="error" class="error-message">{{ error }}</p>

        <p class="auth-link">
          Уже есть аккаунт?
          <router-link to="/login">Войти</router-link>
        </p>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '@/api/client' 

const router = useRouter()

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const isLoading = ref(false)
const error = ref('')

async function handleRegister() {
  // Проверка совпадения паролей
  if (password.value !== confirmPassword.value) {
    error.value = 'Пароли не совпадают'
    return
  }

  isLoading.value = true
  error.value = ''

  try {
    console.log('🔹 Starting registration:', { email: email.value })

    // 1. Регистрируем пользователя через authApi
    const registerResponse = await authApi.register(email.value, password.value)
    
    console.log('✅ Registration response:', registerResponse.data)
    
    // 2. Извлекаем user_id из ответа
    const userId = registerResponse.data?.user_id
    if (!userId) {
      throw new Error('Сервер не вернул user_id')
    }
    
    // 3. Сохраняем данные в localStorage
    localStorage.setItem('user_id', String(userId))
    localStorage.setItem('user_email', email.value)
    console.log('💾 Saved to localStorage:', { user_id: userId, email: email.value })
    
    // 4. Пробуем автоматически войти
    try {
      const loginResponse = await authApi.login(email.value, password.value)
      if (loginResponse.data.access_token) {
        localStorage.setItem('access_token', loginResponse.data.access_token)
        console.log('💾 Saved access_token')
      }
    } catch (loginErr) {
      // Если вход не удался — не блокируем процесс, просто логируем
      console.warn('⚠️ Auto-login skipped or failed:', loginErr)
    }
    
    // 5. Перенаправляем на главную
    console.log('🔹 Redirecting to /')
    router.push('/')
    
  } catch (err: any) {
    console.error('❌ Registration error:', err)
    
    // Формируем понятное сообщение об ошибке
    if (err.response?.status === 400) {
      error.value = err.response.data?.detail || 'Email уже зарегистрирован'
    } else if (err.response?.status === 404) {
      error.value = 'Сервер не найден. Проверь, запущен ли бэкенд.'
    } else if (err.code === 'ERR_NETWORK') {
      error.value = 'Не удалось соединиться с сервером'
    } else {
      error.value = err.message || 'Ошибка регистрации'
    }
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.auth-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 8px;
}

.auth-logo-icon {
  width: 350px;
  height: 150px;
  object-fit: contain;
}

.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.auth-card {
  background: white;
  padding: 40px;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  width: 100%;
  max-width: 400px;
}

.auth-subtitle {
  text-align: center;
  color: #718096;
  margin-bottom: 32px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 600;
  color: #4a5568;
  font-size: 0.9rem;
}

.form-group input {
  padding: 12px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 14px;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, opacity 0.2s;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  color: #e53e3e;
  text-align: center;
  font-size: 0.9rem;
}

.auth-link {
  text-align: center;
  color: #718096;
  font-size: 0.9rem;
}

.auth-link a {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
}

.auth-link a:hover {
  text-decoration: underline;
}
</style>