<template>
  <div id="app">
    <!-- Хедер показываем только на защищённых роутах -->
    <AppHeader v-if="showHeader" />
    
    <!-- Основной контент -->
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'

const route = useRoute()

// Показываем хедер только на защищённых роутах 
const showHeader = computed(() => {
  return route.meta.requiresAuth === true
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  min-height: 100vh;
}
</style>