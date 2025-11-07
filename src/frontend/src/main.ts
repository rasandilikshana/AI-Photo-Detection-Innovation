import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import './style.css'
import App from './App.vue'
import Home from './views/Home.vue'
import { useAuthStore } from './stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: Home,
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('./views/Login.vue'),
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('./views/Register.vue'),
    },
    {
      path: '/competitions',
      name: 'Competitions',
      component: () => import('./views/Competitions.vue'),
    },
    {
      path: '/competitions/:id',
      name: 'CompetitionDetail',
      component: () => import('./views/CompetitionDetail.vue'),
    },
    {
      path: '/submit/:competitionId',
      name: 'Submit',
      component: () => import('./views/Submit.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/my-submissions',
      name: 'MySubmissions',
      component: () => import('./views/MySubmissions.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

// Navigation guard for auth
router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  // Try to fetch current user if we have a token
  if (localStorage.getItem('access_token') && !authStore.user) {
    await authStore.fetchCurrentUser()
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

const pinia = createPinia()
const app = createApp(App)

app.use(pinia)
app.use(router)
app.mount('#app')
