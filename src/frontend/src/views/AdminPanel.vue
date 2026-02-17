<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import apiClient from '@/api/client'

interface User {
  id: number
  email: string
  username: string
  full_name: string
  role: string
  is_active: boolean
  is_verified: boolean
  created_at: string
}

interface Competition {
  id: number
  title: string
  status: string
  submission_start: string
  submission_end: string
  organizer_id: number
}

const router = useRouter()
const authStore = useAuthStore()

// State
const activeTab = ref<'users' | 'competitions' | 'stats'>('stats')
const users = ref<User[]>([])
const competitions = ref<Competition[]>([])
const isLoading = ref(true)
const error = ref('')
const success = ref('')

// Stats
const stats = ref({
  totalUsers: 0,
  totalCompetitions: 0,
  totalSubmissions: 0,
  activeCompetitions: 0,
})

// Check if user is admin
const isAdmin = computed(() => {
  return authStore.user?.role === 'admin'
})

onMounted(async () => {
  if (!isAdmin.value) {
    router.push('/')
    return
  }

  await loadStats()
})

const loadStats = async () => {
  try {
    isLoading.value = true
    error.value = ''

    // Load users count
    const usersResponse = await apiClient.get('/users')
    stats.value.totalUsers = usersResponse.data.length
    users.value = usersResponse.data

    // Load competitions
    const compsResponse = await apiClient.get('/competitions')
    stats.value.totalCompetitions = compsResponse.data.length
    stats.value.activeCompetitions = compsResponse.data.filter(
      (c: Competition) => c.status === 'open' || c.status === 'judging'
    ).length
    competitions.value = compsResponse.data

    // Load submissions count (from users' submissions)
    const subsResponse = await apiClient.get('/submissions')
    stats.value.totalSubmissions = subsResponse.data.length
  } catch (err) {
    error.value = 'Failed to load admin data'
    console.error('Failed to load admin data:', err)
  } finally {
    isLoading.value = false
  }
}

const updateUserRole = async (userId: number, newRole: string) => {
  try {
    error.value = ''
    success.value = ''
    // Note: This would require a backend endpoint to update user roles
    // For now, show a placeholder message
    success.value = `Role update for user ${userId} to ${newRole} would be processed here`

    // In production, you would call:
    // await apiClient.patch(`/users/${userId}`, { role: newRole })
    // await loadStats()
  } catch (err) {
    error.value = 'Failed to update user role'
  }
}

const toggleUserStatus = async (userId: number, isActive: boolean) => {
  try {
    error.value = ''
    success.value = ''
    success.value = `User ${userId} status would be set to ${isActive ? 'active' : 'inactive'}`
  } catch (err) {
    error.value = 'Failed to update user status'
  }
}

const getRoleBadgeClass = (role: string) => {
  const classes: Record<string, string> = {
    admin: 'bg-red-500',
    organizer: 'bg-purple-500',
    judge: 'bg-blue-500',
    participant: 'bg-green-500',
  }
  return classes[role] || 'bg-gray-500'
}

const getStatusBadgeClass = (status: string) => {
  const classes: Record<string, string> = {
    open: 'bg-green-500',
    judging: 'bg-blue-500',
    closed: 'bg-gray-500',
    completed: 'bg-purple-500',
    draft: 'bg-yellow-500',
  }
  return classes[status] || 'bg-gray-500'
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString()
}
</script>

<template>
  <div class="container mx-auto px-4 py-12">
    <div class="mb-8">
      <h1 class="text-4xl font-bold tracking-tight mb-4">Admin Panel</h1>
      <p class="text-lg text-muted-foreground">
        Manage users, competitions, and system settings
      </p>
    </div>

    <!-- Not admin warning -->
    <Alert v-if="!isAdmin" variant="destructive" class="mb-6">
      <AlertDescription>
        You don't have admin permissions.
      </AlertDescription>
    </Alert>

    <!-- Error/Success alerts -->
    <Alert v-if="error" variant="destructive" class="mb-6">
      <AlertDescription>{{ error }}</AlertDescription>
    </Alert>

    <Alert v-if="success" class="mb-6 bg-green-50 text-green-800 border-green-200">
      <AlertDescription>{{ success }}</AlertDescription>
    </Alert>

    <!-- Loading state -->
    <div v-if="isLoading" class="text-center py-12">
      <p class="text-muted-foreground">Loading admin data...</p>
    </div>

    <template v-else-if="isAdmin">
      <!-- Tab Navigation -->
      <div class="flex gap-2 mb-8 border-b">
        <Button
          variant="ghost"
          :class="{ 'border-b-2 border-primary': activeTab === 'stats' }"
          @click="activeTab = 'stats'"
        >
          Dashboard
        </Button>
        <Button
          variant="ghost"
          :class="{ 'border-b-2 border-primary': activeTab === 'users' }"
          @click="activeTab = 'users'"
        >
          Users
        </Button>
        <Button
          variant="ghost"
          :class="{ 'border-b-2 border-primary': activeTab === 'competitions' }"
          @click="activeTab = 'competitions'"
        >
          Competitions
        </Button>
      </div>

      <!-- Stats Tab -->
      <div v-if="activeTab === 'stats'" class="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader class="pb-2">
            <CardDescription>Total Users</CardDescription>
            <CardTitle class="text-4xl">{{ stats.totalUsers }}</CardTitle>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader class="pb-2">
            <CardDescription>Total Competitions</CardDescription>
            <CardTitle class="text-4xl">{{ stats.totalCompetitions }}</CardTitle>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader class="pb-2">
            <CardDescription>Active Competitions</CardDescription>
            <CardTitle class="text-4xl">{{ stats.activeCompetitions }}</CardTitle>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader class="pb-2">
            <CardDescription>Total Submissions</CardDescription>
            <CardTitle class="text-4xl">{{ stats.totalSubmissions }}</CardTitle>
          </CardHeader>
        </Card>

        <!-- Quick Actions -->
        <Card class="md:col-span-2 lg:col-span-4">
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent class="flex gap-4 flex-wrap">
            <Button @click="router.push('/competitions')">View Competitions</Button>
            <Button variant="outline" @click="loadStats">Refresh Stats</Button>
          </CardContent>
        </Card>
      </div>

      <!-- Users Tab -->
      <div v-if="activeTab === 'users'">
        <Card>
          <CardHeader>
            <CardTitle>User Management</CardTitle>
            <CardDescription>{{ users.length }} users registered</CardDescription>
          </CardHeader>
          <CardContent>
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b">
                    <th class="text-left py-3 px-4">User</th>
                    <th class="text-left py-3 px-4">Role</th>
                    <th class="text-left py-3 px-4">Status</th>
                    <th class="text-left py-3 px-4">Joined</th>
                    <th class="text-left py-3 px-4">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="user in users" :key="user.id" class="border-b">
                    <td class="py-3 px-4">
                      <div>
                        <p class="font-medium">{{ user.username }}</p>
                        <p class="text-muted-foreground text-xs">{{ user.email }}</p>
                      </div>
                    </td>
                    <td class="py-3 px-4">
                      <Badge :class="getRoleBadgeClass(user.role)">
                        {{ user.role.toUpperCase() }}
                      </Badge>
                    </td>
                    <td class="py-3 px-4">
                      <Badge :class="user.is_active ? 'bg-green-500' : 'bg-red-500'">
                        {{ user.is_active ? 'Active' : 'Inactive' }}
                      </Badge>
                    </td>
                    <td class="py-3 px-4">{{ formatDate(user.created_at) }}</td>
                    <td class="py-3 px-4">
                      <div class="flex gap-2">
                        <select
                          class="text-xs border rounded px-2 py-1"
                          :value="user.role"
                          @change="updateUserRole(user.id, ($event.target as HTMLSelectElement).value)"
                        >
                          <option value="participant">Participant</option>
                          <option value="judge">Judge</option>
                          <option value="organizer">Organizer</option>
                          <option value="admin">Admin</option>
                        </select>
                        <Button
                          size="sm"
                          variant="outline"
                          @click="toggleUserStatus(user.id, !user.is_active)"
                        >
                          {{ user.is_active ? 'Disable' : 'Enable' }}
                        </Button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- Competitions Tab -->
      <div v-if="activeTab === 'competitions'">
        <Card>
          <CardHeader>
            <CardTitle>Competition Management</CardTitle>
            <CardDescription>{{ competitions.length }} competitions</CardDescription>
          </CardHeader>
          <CardContent>
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b">
                    <th class="text-left py-3 px-4">Competition</th>
                    <th class="text-left py-3 px-4">Status</th>
                    <th class="text-left py-3 px-4">Dates</th>
                    <th class="text-left py-3 px-4">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="comp in competitions" :key="comp.id" class="border-b">
                    <td class="py-3 px-4">
                      <p class="font-medium">{{ comp.title }}</p>
                    </td>
                    <td class="py-3 px-4">
                      <Badge :class="getStatusBadgeClass(comp.status)">
                        {{ comp.status.toUpperCase() }}
                      </Badge>
                    </td>
                    <td class="py-3 px-4">
                      {{ formatDate(comp.submission_start) }} - {{ formatDate(comp.submission_end) }}
                    </td>
                    <td class="py-3 px-4">
                      <div class="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          @click="router.push(`/competitions/${comp.id}`)"
                        >
                          View
                        </Button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </template>
  </div>
</template>
