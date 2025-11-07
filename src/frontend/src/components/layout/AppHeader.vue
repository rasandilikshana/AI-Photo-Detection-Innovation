<template>
  <v-app-bar app elevation="2" color="primary">
    <v-container fluid class="d-flex align-center px-4">
      <!-- Logo and Title -->
      <router-link to="/" class="d-flex align-center text-decoration-none">
        <v-icon size="32" color="white" class="mr-2">mdi-camera-iris</v-icon>
        <v-toolbar-title class="text-white font-weight-bold">
          {{ appName }}
        </v-toolbar-title>
      </router-link>

      <v-spacer />

      <!-- Navigation Menu (Desktop) -->
      <div v-if="!mobile" class="d-flex align-center">
        <v-btn
          v-for="item in visibleNavItems"
          :key="item.path"
          :to="item.path"
          variant="text"
          color="white"
          class="mx-1"
        >
          <v-icon start>{{ item.icon }}</v-icon>
          {{ item.title }}
        </v-btn>

        <!-- User Menu (Authenticated) -->
        <v-menu v-if="authStore.isAuthenticated" offset-y>
          <template #activator="{ props }">
            <v-btn v-bind="props" variant="text" color="white" class="ml-2">
              <v-icon start>mdi-account-circle</v-icon>
              {{ authStore.user?.username }}
              <v-icon end>mdi-menu-down</v-icon>
            </v-btn>
          </template>
          <v-list>
            <v-list-item :to="{ name: 'profile' }">
              <template #prepend>
                <v-icon>mdi-account</v-icon>
              </template>
              <v-list-item-title>Profile</v-list-item-title>
            </v-list-item>
            <v-list-item :to="{ name: 'participant-dashboard' }">
              <template #prepend>
                <v-icon>mdi-view-dashboard</v-icon>
              </template>
              <v-list-item-title>Dashboard</v-list-item-title>
            </v-list-item>
            <v-divider />
            <v-list-item @click="handleLogout">
              <template #prepend>
                <v-icon color="error">mdi-logout</v-icon>
              </template>
              <v-list-item-title class="text-error">Logout</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>

        <!-- Auth Buttons (Not Authenticated) -->
        <div v-else class="d-flex ml-2">
          <v-btn :to="{ name: 'login' }" variant="text" color="white" class="mr-2">
            Login
          </v-btn>
          <v-btn :to="{ name: 'register' }" variant="flat" color="accent">
            Sign Up
          </v-btn>
        </div>
      </div>

      <!-- Mobile Menu Button -->
      <v-app-bar-nav-icon v-if="mobile" color="white" @click="emit('toggle-drawer')" />
    </v-container>
  </v-app-bar>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDisplay } from 'vuetify'
import { useAuthStore } from '@/store/auth'
import { useToast } from 'vue-toastification'

const router = useRouter()
const authStore = useAuthStore()
const { mobile } = useDisplay()
const toast = useToast()

const emit = defineEmits<{
  'toggle-drawer': []
}>()

const appName = import.meta.env.VITE_APP_NAME || 'A.V.A.R'

// Navigation items based on authentication status
const navItems = computed(() => {
  const items = [
    { title: 'Home', path: '/', icon: 'mdi-home', auth: false },
    { title: 'Competitions', path: '/competitions', icon: 'mdi-trophy', auth: false },
  ]

  if (authStore.isAuthenticated) {
    items.push({
      title: 'My Submissions',
      path: '/submissions/my',
      icon: 'mdi-image-multiple',
      auth: true,
    })

    if (authStore.isOrganizer) {
      items.push({
        title: 'Create Competition',
        path: '/competitions/create',
        icon: 'mdi-plus-circle',
        auth: true,
      })
    }

    if (authStore.isAdmin) {
      items.push({
        title: 'Admin',
        path: '/admin',
        icon: 'mdi-shield-crown',
        auth: true,
      })
    }
  }

  return items
})

const visibleNavItems = computed(() => {
  return navItems.value.filter((item) => {
    if (item.auth && !authStore.isAuthenticated) return false
    return true
  })
})

async function handleLogout() {
  try {
    authStore.logout()
    toast.success('Logged out successfully')
    router.push({ name: 'home' })
  } catch (error) {
    toast.error('Failed to logout')
  }
}
</script>

<style scoped>
.v-toolbar-title {
  font-size: 1.5rem;
  letter-spacing: 0.5px;
}
</style>
