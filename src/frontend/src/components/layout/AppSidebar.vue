<template>
  <v-navigation-drawer
    :model-value="modelValue"
    temporary
    location="left"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <!-- User Profile Section -->
    <template v-if="authStore.isAuthenticated">
      <v-list>
        <v-list-item
          :prepend-avatar="userAvatar"
          :title="authStore.user?.full_name || authStore.user?.username"
          :subtitle="authStore.user?.email"
        >
          <template #append>
            <v-chip :color="roleColor" size="small" variant="flat">
              {{ authStore.user?.role }}
            </v-chip>
          </template>
        </v-list-item>
      </v-list>
      <v-divider />
    </template>

    <!-- Navigation Menu -->
    <v-list nav density="comfortable">
      <v-list-item
        v-for="item in visibleNavItems"
        :key="item.path"
        :to="item.path"
        :prepend-icon="item.icon"
        :title="item.title"
        color="primary"
      />
    </v-list>

    <v-divider />

    <!-- User Actions -->
    <template v-if="authStore.isAuthenticated">
      <v-list nav density="comfortable">
        <v-list-item
          :to="{ name: 'profile' }"
          prepend-icon="mdi-account"
          title="Profile"
          color="primary"
        />
        <v-list-item
          :to="dashboardRoute"
          prepend-icon="mdi-view-dashboard"
          title="Dashboard"
          color="primary"
        />
        <v-list-item
          prepend-icon="mdi-logout"
          title="Logout"
          color="error"
          @click="handleLogout"
        />
      </v-list>
    </template>
    <template v-else>
      <v-list nav density="comfortable">
        <v-list-item
          :to="{ name: 'login' }"
          prepend-icon="mdi-login"
          title="Login"
          color="primary"
        />
        <v-list-item
          :to="{ name: 'register' }"
          prepend-icon="mdi-account-plus"
          title="Sign Up"
          color="accent"
        />
      </v-list>
    </template>
  </v-navigation-drawer>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { useToast } from 'vue-toastification'

interface Props {
  modelValue: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const router = useRouter()
const authStore = useAuthStore()
const toast = useToast()

const userAvatar = computed(() => {
  // Generate avatar from username initials
  const username = authStore.user?.username || 'U'
  return `https://ui-avatars.com/api/?name=${username}&background=1976D2&color=fff`
})

const roleColor = computed(() => {
  switch (authStore.user?.role) {
    case 'admin':
      return 'error'
    case 'organizer':
      return 'warning'
    case 'judge':
      return 'info'
    default:
      return 'success'
  }
})

const dashboardRoute = computed(() => {
  if (authStore.isAdmin) return { name: 'admin-dashboard' }
  if (authStore.isJudge) return { name: 'judge-dashboard' }
  if (authStore.isOrganizer) return { name: 'organizer-dashboard' }
  return { name: 'participant-dashboard' }
})

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
        title: 'My Competitions',
        path: '/organizer/competitions',
        icon: 'mdi-briefcase',
        auth: true,
      })
      items.push({
        title: 'Create Competition',
        path: '/competitions/create',
        icon: 'mdi-plus-circle',
        auth: true,
      })
    }

    if (authStore.isAdmin) {
      items.push({
        title: 'Admin Panel',
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
    emit('update:modelValue', false)
    router.push({ name: 'home' })
  } catch (error) {
    toast.error('Failed to logout')
  }
}
</script>
