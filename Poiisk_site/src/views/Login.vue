<template>
  <div class="auth-container">
    <div class="auth-card">
      <div class="auth-header">
        <img src="@/assets/poiisk.png" alt="ПоИИск" class="auth-logo-icon" />
      </div>
      <h2 class="auth-subtitle">Вход</h2>

      <form @submit.prevent="handleLogin" class="auth-form">
        <div class="form-group">
          <label>Email</label>
          <input
            v-model="email"
            type="email"
            placeholder="your@email.com"
            required
          />
        </div>

        <div class="form-group">
          <label>Пароль</label>
          <input
            v-model="password"
            type="password"
            placeholder="••••••••"
            required
          />
        </div>

        <button type="submit" :disabled="isLoading">
          {{ isLoading ? 'Вход...' : 'Войти' }}
        </button>

        <p v-if="error" class="error">{{ error }}</p>

        <p class="link">
          Нет аккаунта?
          <router-link to="/register">Зарегистрироваться</router-link>
        </p>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const email = ref('')
const password = ref('')
const isLoading = ref(false)
const error = ref('')

async function handleLogin() {
  isLoading.value = true
  error.value = ''

  try {
    console.log('🔹 Login attempt:', email.value)

    // Прямой fetch
    const response = await fetch('http://127.0.0.1:8000/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: `username=${encodeURIComponent(email.value)}&password=${encodeURIComponent(password.value)}`,
    })

    console.log('🔹 Response status:', response.status)

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Неверный email или пароль')
      }
      throw new Error(`Ошибка сервера: ${response.status}`)
    }

    const data = await response.json()
    console.log('Login success:', data)

    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('user_id', String(data.user_id))
    localStorage.setItem('user_email', data.email)

    const savedToken = localStorage.getItem('access_token')
    console.log('Token saved:', savedToken)

    if (!savedToken) {
      console.error('Failed to save token!')
      throw new Error('Не удалось сохранить токен')
    }

    await new Promise(resolve => setTimeout(resolve, 100))

    console.log('🔹 About to redirect to /')
    console.log('🔹 localStorage check:', {
      token: localStorage.getItem('access_token'),
      user_id: localStorage.getItem('user_id')
    })

    // Редирект на чат
    await router.push('/')
    console.log('Redirected')

  } catch (err: any) {
    console.error('Login error:', err)
    error.value = err.message || 'Ошибка соединения с сервером'
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

.auth-subtitle {
  text-align: center;
  color: #718096;
  margin-bottom: 32px;
}

.auth-card {
  background: white;
  padding: 40px;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  width: 100%;
  max-width: 400px;
}

h1 {
  text-align: center;
  margin-bottom: 8px;
  color: #2d3748;
  font-size: 2rem;
}

.subtitle {
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

button {
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

button:hover:not(:disabled) {
  transform: translateY(-2px);
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error {
  color: #e53e3e;
  text-align: center;
  font-size: 0.9rem;
}

.link {
  text-align: center;
  color: #718096;
  font-size: 0.9rem;
}

.link a {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
}

.link a:hover {
  text-decoration: underline;
}
</style>