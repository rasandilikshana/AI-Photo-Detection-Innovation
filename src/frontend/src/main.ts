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
    {
      path: '/judge',
      name: 'JudgeDashboard',
      component: () => import('./views/JudgeDashboard.vue'),
      meta: { requiresAuth: true, requiresJudge: true },
    },
    {
      path: '/judge/score/:submissionId',
      name: 'ScoreSubmission',
      component: () => import('./views/ScoreSubmission.vue'),
      meta: { requiresAuth: true, requiresJudge: true },
    },
    {
      path: '/admin',
      name: 'AdminPanel',
      component: () => import('./views/AdminPanel.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/organizer',
      name: 'OrganizerPanel',
      component: () => import('./views/OrganizerPanel.vue'),
      meta: { requiresAuth: true, requiresOrganizer: true },
    },
  ],
})

// Navigation guard for auth and role-based access
router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  // Try to fetch current user if we have a token
  if (localStorage.getItem('access_token') && !authStore.user) {
    await authStore.fetchCurrentUser()
  }

  // Redirect authenticated users away from login/register pages
  if ((to.name === 'Login' || to.name === 'Register') && authStore.isAuthenticated) {
    next({ name: 'Competitions' })
    return
  }

  // Check authentication
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  // Check judge role
  if (to.meta.requiresJudge) {
    const userRole = authStore.user?.role
    if (userRole !== 'judge' && userRole !== 'admin') {
      next({ name: 'Home' })
      return
    }
  }

  // Check admin role
  if (to.meta.requiresAdmin) {
    if (authStore.user?.role !== 'admin') {
      next({ name: 'Home' })
      return
    }
  }

  // Check organizer role
  if (to.meta.requiresOrganizer) {
    const userRole = authStore.user?.role
    if (userRole !== 'organizer' && userRole !== 'admin') {
      next({ name: 'Home' })
      return
    }
  }

  next()
})

const pinia = createPinia()
const app = createApp(App)

app.use(pinia)
app.use(router)
app.mount('#app')
