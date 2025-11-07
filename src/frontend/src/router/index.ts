/**
 * Vue Router Configuration
 * Defines all application routes with lazy loading and route guards
 */

import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/Home.vue'),
    meta: { requiresAuth: false },
  },

  // Authentication Routes
  {
    path: '/auth',
    component: () => import('@/views/auth/AuthLayout.vue'),
    children: [
      {
        path: 'login',
        name: 'login',
        component: () => import('@/views/auth/Login.vue'),
        meta: { requiresAuth: false, hideForAuth: true },
      },
      {
        path: 'register',
        name: 'register',
        component: () => import('@/views/auth/Register.vue'),
        meta: { requiresAuth: false, hideForAuth: true },
      },
    ],
  },

  // Competition Routes
  {
    path: '/competitions',
    name: 'competitions',
    component: () => import('@/views/competitions/Browse.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/competitions/:slug',
    name: 'competition-detail',
    component: () => import('@/views/competitions/Detail.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/competitions/create',
    name: 'competition-create',
    component: () => import('@/views/competitions/Create.vue'),
    meta: { requiresAuth: true, roles: ['organizer', 'admin'] },
  },

  // Submission Routes
  {
    path: '/competitions/:slug/submit',
    name: 'submission-create',
    component: () => import('@/views/submissions/Create.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/submissions',
    name: 'my-submissions',
    component: () => import('@/views/submissions/MySubmissions.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/submissions/:id',
    name: 'submission-detail',
    component: () => import('@/views/submissions/Detail.vue'),
    meta: { requiresAuth: true },
  },

  // Dashboard Routes
  {
    path: '/dashboard',
    name: 'dashboard',
    redirect: (to) => {
      const authStore = useAuthStore()
      const role = authStore.user?.role

      if (role === 'admin') return { name: 'admin-dashboard' }
      if (role === 'organizer') return { name: 'organizer-dashboard' }
      if (role === 'judge') return { name: 'judge-dashboard' }
      return { name: 'participant-dashboard' }
    },
    meta: { requiresAuth: true },
  },
  {
    path: '/dashboard/participant',
    name: 'participant-dashboard',
    component: () => import('@/views/dashboard/Participant.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/dashboard/organizer',
    name: 'organizer-dashboard',
    component: () => import('@/views/dashboard/Organizer.vue'),
    meta: { requiresAuth: true, roles: ['organizer', 'admin'] },
  },
  {
    path: '/dashboard/judge',
    name: 'judge-dashboard',
    component: () => import('@/views/dashboard/Judge.vue'),
    meta: { requiresAuth: true, roles: ['judge', 'admin'] },
  },

  // Admin Routes
  {
    path: '/admin',
    name: 'admin-dashboard',
    component: () => import('@/views/admin/Dashboard.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },

  // Profile
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/views/Profile.vue'),
    meta: { requiresAuth: true },
  },

  // Error Routes
  {
    path: '/403',
    name: 'forbidden',
    component: () => import('@/views/errors/Forbidden.vue'),
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/errors/NotFound.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  },
})

// Navigation guards
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)
  const hideForAuth = to.matched.some((record) => record.meta.hideForAuth)
  const requiredRoles = to.meta.roles as string[] | undefined

  // Redirect authenticated users away from login/register
  if (hideForAuth && authStore.isAuthenticated) {
    next({ name: 'dashboard' })
    return
  }

  // Check authentication
  if (requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }

  // Check role-based access
  if (requiredRoles && authStore.user) {
    const hasRequiredRole = requiredRoles.includes(authStore.user.role)
    if (!hasRequiredRole) {
      next({ name: 'forbidden' })
      return
    }
  }

  next()
})

export default router
