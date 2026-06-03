// src/router/index.ts
import { createRouter, createWebHistory, type RouteLocationNormalized } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/Register.vue'),
    },
    {
      path: '/chat',
      name: 'Chat',
      component: () => import('@/views/ChatView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/resume',
      name: 'Resume',
      component: () => import('@/views/ResumeView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/favorites',
      name: 'Favorites',
      component: () => import('@/views/FavoritesView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/profile',
      name: 'Profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/',
      redirect: '/chat',
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      redirect: '/chat',
    },
  ],
})

router.beforeEach((to: RouteLocationNormalized, from, next) => {
  const token = localStorage.getItem('access_token')
  
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if ((to.path === '/login' || to.path === '/register') && token) {
    next('/')
  } else {
    next()
  }
})

export default router