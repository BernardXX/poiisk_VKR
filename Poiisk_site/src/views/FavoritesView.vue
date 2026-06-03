<template>
  <div class="page-container">
    <div class="favorites-header">
      <h1>⭐ Избранные вакансии</h1>
      <div class="favorites-controls">
        <select v-model="sortBy" class="sort-select" @change="sortVacancies">
          <option value="date">🕐 По дате сохранения</option>
          <option value="salary">💰 По зарплате</option>
          <option value="company">🏢 По компании</option>
        </select>
      </div>
    </div>

    <!-- Загрузка -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Загружаем избранные вакансии...</p>
    </div>

    <!-- Пустой список -->
    <div v-else-if="favorites.length === 0" class="empty-state">
      <div class="empty-icon">📭</div>
      <h2>Пока нет избранных вакансий</h2>
      <p>Сохраняйте интересные вакансии из чата, чтобы вернуться к ним позже</p>
      <button @click="$router.push('/chat')" class="btn-primary">
        🔍 Начать поиск вакансий
      </button>
    </div>

    <!-- Список вакансий -->
    <div v-else class="favorites-list">
      <div 
        v-for="vacancy in sortedFavorites" 
        :key="vacancy.vacancy_id"
        class="favorite-card"
      >
        <div class="favorite-card-header">
          <div class="vacancy-info">
            <h3 class="vacancy-title">{{ vacancy.title }}</h3>
            <p class="vacancy-company">🏢 {{ vacancy.company }}</p>
          </div>
          <button 
            @click="removeFromFavorites(vacancy.vacancy_id, vacancy.url)" 
            class="btn-remove"
            title="Удалить из избранного"
          >
            ✕
          </button>
        </div>

        <div class="vacancy-details">
          <!-- Зарплата -->
          <div v-if="vacancy.salary_snapshot && vacancy.salary_snapshot !== 'Не указана'" class="vacancy-salary">
            💰 {{ vacancy.salary_snapshot }}
          </div>
          <div v-else class="vacancy-salary empty">
            💰 Зарплата не указана
          </div>

        </div>

        <div class="vacancy-footer">
          <span class="saved-date">
            🕐 Сохранено: {{ formatDate(vacancy.saved_at) }}
          </span>
          <a :href="vacancy.url" target="_blank" class="btn-open">
            Открыть вакансию ↗
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

interface FavoriteVacancy {
  vacancy_id: number
  hh_vacancy_id: number
  title: string
  company: string
  url: string
  salary_snapshot: string | null
  location_snapshot: string | null
  saved_at: string
  status: string
}

const router = useRouter()
const loading = ref(true)
const favorites = ref<FavoriteVacancy[]>([])
const sortBy = ref('date')

const userId = computed(() => {
  const id = localStorage.getItem('user_id')
  return id ? parseInt(id, 10) : 1
})

// Сортировка вакансий
const sortedFavorites = computed(() => {
  const list = [...favorites.value]
  
  switch (sortBy.value) {
    case 'salary':
      return list.sort((a, b) => {
        const getSalaryNum = (s: string | null) => {
          if (!s || s === 'Не указана') return 0
          const num = parseInt(s.replace(/\D/g, ''))
          return num || 0
        }
        return getSalaryNum(b.salary_snapshot) - getSalaryNum(a.salary_snapshot)
      })
    case 'company':
      return list.sort((a, b) => a.company.localeCompare(b.company))
    case 'date':
    default:
      return list.sort((a, b) => 
        new Date(b.saved_at).getTime() - new Date(a.saved_at).getTime()
      )
  }
})

function sortVacancies() {
  // Вычисляемое свойство автоматически пересчитается
}

// Форматирование локации
function formatLocation(location: string): string {
  if (!location || location === 'no_match') return ''
  return location
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase())
}

// Загрузка избранных вакансий
async function loadFavorites() {
  loading.value = true
  try {
    const uid = userId.value
    const response = await fetch(`http://127.0.0.1:8000/api/favorites?user_id=${uid}`)
    
    if (response.ok) {
      favorites.value = await response.json()
    } else {
      console.error('Failed to load favorites')
    }
  } catch (err) {
    console.error('Error loading favorites:', err)
  } finally {
    loading.value = false
  }
}

// Удаление из избранного
async function removeFromFavorites(vacancyId: number, vacancyUrl: string) {
  
  try {
    const uid = userId.value
    const response = await fetch(
      `http://127.0.0.1:8000/api/favorites?user_id=${uid}&vacancy_url=${encodeURIComponent(vacancyUrl)}`,
      { method: 'DELETE' }
    )
    
    if (response.ok) {
      favorites.value = favorites.value.filter(v => v.vacancy_id !== vacancyId)
    } else {
      alert('❌ Ошибка при удалении')
    }
  } catch (err) {
    console.error('Error removing favorite:', err)
    alert('❌ Ошибка сети')
  }
}

// Форматирование даты
function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadFavorites()
})
</script>

<style scoped>
.page-container {
  padding: 32px 24px;
  max-width: 1000px;
  margin: 0 auto;
}

.favorites-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  flex-wrap: wrap;
  gap: 16px;
}

.favorites-header h1 {
  margin: 0;
  color: #2d3748;
  font-size: 2rem;
}

.favorites-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sort-select {
  padding: 10px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  font-size: 0.95rem;
  background: white;
  cursor: pointer;
  transition: border-color 0.2s;
}

.sort-select:focus {
  outline: none;
  border-color: #667eea;
}

.loading-state {
  text-align: center;
  padding: 80px 20px;
  color: #4a5568;
}

.loading-state .spinner {
  margin: 0 auto 20px;
}

.empty-state {
  text-align: center;
  padding: 100px 20px;
  color: #718096;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state h2 {
  margin: 0 0 12px 0;
  color: #2d3748;
  font-size: 1.5rem;
}

.empty-state p {
  margin: 0 0 24px 0;
  font-size: 1rem;
}

.empty-state .btn-primary {
  padding: 12px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.empty-state .btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

/* Список вакансий */
.favorites-list {
  display: grid;
  gap: 20px;
}

.favorite-card {
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 14px;
  padding: 24px;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.favorite-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  transform: translateY(-3px);
  border-color: #667eea;
}

.favorite-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  gap: 16px;
}

.vacancy-title {
  font-size: 1.25rem;
  color: #2d3748;
  margin: 0 0 6px 0;
  font-weight: 700;
  line-height: 1.3;
}

.vacancy-company {
  color: #718096;
  font-size: 1rem;
  margin: 0;
}

.btn-remove {
  width: 36px;
  height: 36px;
  border: none;
  background: #fed7d7;
  color: #c53030;
  border-radius: 8px;
  font-size: 1.1rem;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-remove:hover {
  background: #e53e3e;
  color: white;
  transform: scale(1.1);
}

.vacancy-details {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
  padding: 16px;
  background: #f7fafc;
  border-radius: 10px;
}

.vacancy-salary {
  font-weight: 700;
  color: #48bb78;
  font-size: 1.1rem;
}

.vacancy-salary.empty {
  color: #a0aec0;
  font-weight: 500;
}

.vacancy-location {
  color: #4a5568;
  font-size: 0.95rem;
}

.vacancy-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.saved-date {
  font-size: 0.9rem;
  color: #a0aec0;
}

.btn-open {
  padding: 10px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-open:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e2e8f0;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 640px) {
  .page-container {
    padding: 20px 16px;
  }
  
  .favorites-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .favorites-header h1 {
    font-size: 1.5rem;
  }
  
  .favorite-card-header {
    flex-direction: column;
  }
  
  .vacancy-footer {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .btn-open {
    width: 100%;
    justify-content: center;
  }
}
</style>