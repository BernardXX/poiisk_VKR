<template>
  <div class="vacancy-card">
    <div class="vacancy-header">
      <div class="vacancy-info">
        <h3 class="vacancy-title">{{ vacancy.name }}</h3>
        <p class="vacancy-company">{{ vacancy.company }}</p>
      </div>
      <div class="vacancy-meta">
        <span v-if="vacancy.salary" class="vacancy-salary">{{ vacancy.salary }}</span>

      </div>
    </div>
    
    <div 
      class="vacancy-snippet markdown-body" 
      v-html="parseMarkdown(vacancy.snippet)"
    ></div>
    
    <!-- Совпавшие навыки -->
    <div v-if="vacancy.matched_skills && vacancy.matched_skills.length > 0" class="matched-skills">
      <span class="skills-label">✅ Имеющиеся навыки:</span>
      <div class="skills-tags">
        <span 
          v-for="skill in vacancy.matched_skills.slice(0, 10)" 
          :key="skill" 
          class="skill-tag matched"
        >
          {{ skill }}
        </span>
      </div>
    </div>
    
    <!-- Недостающие навыки -->
    <div v-if="vacancy.missing_skills && vacancy.missing_skills.length > 0" class="missing-skills">
      <span class="skills-label">⚠️ Требуются навыки:</span>
      <div class="skills-tags">
        <span 
          v-for="skill in vacancy.missing_skills.slice(0, 10)" 
          :key="skill" 
          class="skill-tag missing"
        >
          {{ skill }}
        </span>
      </div>
    </div>
    
    <!-- Информация о локации -->
    <div v-if="vacancy.location_match" class="location-info">
      <span v-if="vacancy.location_match === 'remote_match'" class="location-badge remote">
        🌍 Удалённая работа
      </span>
      <span v-else-if="vacancy.location_match === 'location_match'" class="location-badge match">
        📍 Соответствует локации
      </span>
      <span v-else class="location-badge no-match">
        📍 Другой регион
      </span>
    </div>
    
    <div v-if="vacancy.note" class="vacancy-note">
      ℹ️ {{ vacancy.note }}
    </div>
    
    <div class="vacancy-actions">
      <a :href="vacancy.url" target="_blank" class="vacancy-link">
        {{ vacancy.source === 'SuperJob' ? '🟣 Открыть на SuperJob ↗' : '🔵 Открыть на HH.ru ↗' }}
      </a>
      <!-- Кнопка "В избранное" -->
      <button 
        @click="addToFavorites" 
        class="btn-favorite"
        :class="{ active: isFavorite }"
        :title="isFavorite ? 'Удалить из избранного' : 'Добавить в избранное'"
      >
        {{ isFavorite ? '★ В избранном' : '☆ В избранное' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { parseMarkdown } from '@/utils/markdown'

interface Vacancy {
  name: string
  company: string
  url: string
  salary?: string
  snippet: string
  full_description?: string
  relevance_score?: number
  matched_skills?: string[]
  missing_skills?: string[]
  location_match?: string
  note?: string
  id?: number
}

const props = defineProps<{
  vacancy: Vacancy
}>()

const emit = defineEmits(['favorite-added', 'favorite-removed'])

const isFavorite = ref(false)

const relevanceClass = computed(() => {
  const score = props.vacancy.relevance_score || 0
  if (score >= 60) return 'high'
  if (score >= 30) return 'medium'
  return 'low'
})

const relevanceText = computed(() => {
  const score = props.vacancy.relevance_score || 0
  if (score >= 60) return 'Отлично'
  if (score >= 30) return 'Хорошо'
  return 'Требует обучения'
})

onMounted(async () => {
  const userId = localStorage.getItem('user_id')
  if (!userId || !props.vacancy.url) return
  
  try {
    const response = await fetch(
      `http://127.0.0.1:8000/api/favorites/check?user_id=${userId}&vacancy_url=${encodeURIComponent(props.vacancy.url)}`
    )
    if (response.ok) {
      const data = await response.json()
      isFavorite.value = data.is_favorite
    }
  } catch (err) {
    console.error('Failed to check favorite status:', err)
  }
})

async function addToFavorites() {
  const userId = localStorage.getItem('user_id')
  if (!userId || !props.vacancy.url) return
  
  try {
    if (isFavorite.value) {
      // Удаляем из избранного
      const response = await fetch(
        `http://127.0.0.1:8000/api/favorites?user_id=${userId}&vacancy_url=${encodeURIComponent(props.vacancy.url)}`,
        { method: 'DELETE' }
      )
      if (response.ok) {
        isFavorite.value = false
        emit('favorite-removed', props.vacancy)
      }
    } else {
      // Добавляем в избранное
      const response = await fetch('http://127.0.0.1:8000/api/favorites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: parseInt(userId),
          hh_vacancy_id: props.vacancy.id || 0,
          title: props.vacancy.name,
          company: props.vacancy.company,
          url: props.vacancy.url,
          salary_snapshot: props.vacancy.salary || null,
          location_snapshot: props.vacancy.location_match || null
        })
      })
      if (response.ok) {
        isFavorite.value = true
        emit('favorite-added', props.vacancy)
        // alert('✅ Вакансия добавлена в избранное!')
      }
    }
  } catch (err) {
    console.error('Failed to toggle favorite:', err)
    alert('❌ Ошибка при работе с избранным')
  }
}
</script>

<style scoped>
.vacancy-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
  transition: all 0.2s;
}

.vacancy-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.vacancy-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
  gap: 16px;
}

.vacancy-title {
  font-size: 1.1rem;
  color: #2d3748;
  margin: 0 0 4px 0;
  font-weight: 600;
}

.vacancy-company {
  color: #718096;
  font-size: 0.9rem;
  margin: 0;
}

.vacancy-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.vacancy-salary {
  font-weight: 600;
  color: #48bb78;
  font-size: 0.95rem;
}

.relevance-badge {
  font-size: 0.8rem;
  padding: 3px 8px;
  border-radius: 12px;
  font-weight: 600;
}

.relevance-badge.high {
  background: #c6f6d5;
  color: #22543d;
}

.relevance-badge.medium {
  background: #feebc8;
  color: #c05621;
}

.relevance-badge.low {
  background: #fed7d7;
  color: #c53030;
}

.vacancy-snippet {
  color: #4a5568;
  font-size: 0.9rem;
  line-height: 1.6;
  margin-bottom: 12px;
}

.markdown-body :deep(strong) {
  font-weight: 700;
  color: #2d3748;
}

.markdown-body :deep(em) {
  font-style: italic;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 8px 0 8px 24px;
  padding-left: 0;
}

.markdown-body :deep(li) {
  margin-bottom: 4px;
}

.matched-skills {
  margin-bottom: 12px;
  padding: 10px;
  background: #f0fff4;
  border-radius: 8px;
  border-left: 3px solid #48bb78;
}

.skills-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #22543d;
  display: block;
  margin-bottom: 6px;
}

.skills-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.skill-tag.matched {
  background: #e6fffa;
  color: #234e52;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
}

.missing-skills {
  margin-bottom: 12px;
  padding: 10px;
  background: #fff5f5;
  border-radius: 8px;
  border-left: 3px solid #fc8181;
}

.missing-skills .skills-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #c53030;
  display: block;
  margin-bottom: 6px;
}

.skill-tag.missing {
  background: #fed7d7;
  color: #c53030;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
}

.location-info {
  margin-bottom: 12px;
}

.location-badge {
  font-size: 0.85rem;
  padding: 4px 10px;
  border-radius: 6px;
  display: inline-block;
}

.location-badge.remote {
  background: #ebf8ff;
  color: #2b6cb0;
}

.location-badge.match {
  background: #c6f6d5;
  color: #22543d;
}

.location-badge.no-match {
  background: #fed7d7;
  color: #c53030;
}

.vacancy-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.vacancy-link {
  display: inline-block;
  padding: 8px 16px;
  background: #edf2f7;
  color: #2d3748;
  text-decoration: none;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s;
}

.vacancy-link:hover {
  background: #e2e8f0;
  transform: translateY(-1px);
}

.btn-favorite {
  padding: 8px 16px;
  background: white;
  border: 2px solid #cbd5e0;
  color: #4a5568;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-favorite:hover {
  border-color: #667eea;
  color: #667eea;
}

.btn-favorite.active {
  background: #fef5e7;
  border-color: #f6ad55;
  color: #c05621;
}
</style>