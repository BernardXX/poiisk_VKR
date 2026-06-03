<template>
  <header class="app-header">
    <div class="header-content">
      <!-- Логотип -->
      <router-link to="/" class="logo">
        <img src="@/assets/poiisk.png" alt="ПоИИск" class="header-logo-img" />
      </router-link>

      <!-- Навигация -->
      <nav class="nav">
        <router-link 
          v-for="item in navItems" 
          :key="item.path"
          :to="item.path"
          class="nav-link"
          active-class="active"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-text">{{ item.label }}</span>
        </router-link>
      </nav>

      <!-- Пользователь + Выйти -->
      <div class="user-section">
        <span class="user-email">{{ userEmail }}</span>
        <button @click="handleLogout" class="btn-logout">Выйти</button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Навигационные пункты
const navItems = [
  { path: '/chat', label: 'Чат', icon: '💬' },
  { path: '/resume', label: 'Резюме', icon: '📄' },
  { path: '/favorites', label: 'Избранное', icon: '⭐' },
  { path: '/profile', label: 'Профиль', icon: '👤' },
]

// Email пользователя из localStorage
const userEmail = computed(() => {
  return localStorage.getItem('user_email') || 'Пользователь'
})

// Выход из аккаунта
function handleLogout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user_id')
  localStorage.removeItem('user_email')
  localStorage.removeItem('activeSessionId') 
  router.push('/login')
}
</script>

<style scoped>
.logo {
  display: flex;
  align-items: center;
  text-decoration: none;
  transition: opacity 0.2s;
}

.logo:hover {
  opacity: 0.8;
}

.header-logo-img {
  height: 60px; 
  width: auto;
  display: block;
}

.app-header {
  background: white;
  border-bottom: 1px solid #e2e8f0;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.logo {
  font-size: 1.4rem;
  font-weight: 700;
  color: #2d3748;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo:hover {
  color: #667eea;
}

.nav {
  display: flex;
  gap: 8px;
  flex: 1;
  justify-content: center;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  border-radius: 8px;
  color: #4a5568;
  text-decoration: none;
  font-weight: 500;
  font-size: 0.95rem;
  transition: background 0.2s, color 0.2s;
}

.nav-link:hover {
  background: #f7fafc;
  color: #2d3748;
}

.nav-link.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.nav-icon {
  font-size: 1.1rem;
}

.user-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-email {
  color: #718096;
  font-size: 0.9rem;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.btn-logout {
  padding: 8px 16px;
  background: #e53e3e;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.9rem;
  transition: background 0.2s;
}

.btn-logout:hover {
  background: #c53030;
}

@media (max-width: 768px) {
  .header-content {
    flex-wrap: wrap;
    height: auto;
    padding: 12px 0;
  }
  
  .nav {
    order: 3;
    width: 100%;
    justify-content: flex-start;
    overflow-x: auto;
    padding: 8px 0;
  }
  
  .nav-link {
    flex-shrink: 0;
    padding: 8px 12px;
    font-size: 0.9rem;
  }
  
  .user-section {
    order: 2;
    margin-left: auto;
  }
}
</style>