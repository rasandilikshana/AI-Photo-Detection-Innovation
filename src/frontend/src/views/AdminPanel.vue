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
import {
  Users, Trophy, Image, Activity, RefreshCw, Eye, Calendar, Search, X,
  Gavel, Plus, Trash2, Loader2, UserPlus, History, Network, Monitor, User as UserIcon, BarChart3, Shield
} from 'lucide-vue-next'
import apiClient from '@/api/client'
import { useV2AnalyticsStore } from '@/stores/v2Analytics'
import { BiasReportDashboard, CredentialSharingAlert } from '@/components/v2'

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

interface Judge {
  id: number
  username: string
  email: string
  full_name: string
  is_active: boolean
}

interface JudgeAssignment {
  id: number
  judge_id: number
  judge_username: string
  judge_email: string
  competition_id: number
  competition_title: string
  competition_status: string
  is_active: boolean
  created_at: string
}

interface ScoreAuditLog {
  id: number
  action_type: 'create' | 'update' | 'delete'
  composition_score: number | null
  technical_score: number | null
  creativity_score: number | null
  overall_score: number | null
  comments: string | null
  prev_composition_score: number | null
  prev_technical_score: number | null
  prev_creativity_score: number | null
  prev_overall_score: number | null
  prev_comments: string | null
  ip_address: string | null
  user_agent: string | null
  session_id: string | null
  judge_identifier: string | null
  score_id: number | null
  submission_id: number
  judge_id: number
  competition_id: number
  created_at: string
}

interface AuditLogListResponse {
  logs: ScoreAuditLog[]
  total_count: number
  unique_sessions: number
  unique_ips: number
}

const router = useRouter()
const authStore = useAuthStore()
const v2Analytics = useV2AnalyticsStore()

// State
const activeTab = ref<'users' | 'competitions' | 'judges' | 'stats' | 'scoring' | 'v2analytics'>('stats')
const users = ref<User[]>([])
const competitions = ref<Competition[]>([])
const judges = ref<Judge[]>([])
const judgeAssignments = ref<JudgeAssignment[]>([])
const isLoading = ref(true)
const isLoadingJudges = ref(false)
const isAssigning = ref(false)
const error = ref('')
const success = ref('')
const searchQuery = ref('')

// Score audit log state
const auditLogs = ref<ScoreAuditLog[]>([])
const auditLogStats = ref<{ total_count: number; unique_sessions: number; unique_ips: number } | null>(null)
const isLoadingAuditLogs = ref(false)
const selectedAuditCompetitionId = ref<number | null>(null)

// New assignment form
const selectedJudgeId = ref<number | null>(null)
const selectedCompetitionId = ref<number | null>(null)

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

// Filtered users
const filteredUsers = computed(() => {
  if (!searchQuery.value.trim()) return users.value
  const query = searchQuery.value.toLowerCase()
  return users.value.filter(u =>
    u.username.toLowerCase().includes(query) ||
    u.email.toLowerCase().includes(query) ||
    u.full_name?.toLowerCase().includes(query)
  )
})

// Filtered competitions
const filteredCompetitions = computed(() => {
  if (!searchQuery.value.trim()) return competitions.value
  const query = searchQuery.value.toLowerCase()
  return competitions.value.filter(c =>
    c.title.toLowerCase().includes(query)
  )
})

// Group assignments by competition
const assignmentsByCompetition = computed(() => {
  const grouped: Record<number, { competition: { id: number; title: string; status: string }; assignments: JudgeAssignment[] }> = {}

  for (const assignment of judgeAssignments.value) {
    if (!grouped[assignment.competition_id]) {
      grouped[assignment.competition_id] = {
        competition: {
          id: assignment.competition_id,
          title: assignment.competition_title,
          status: assignment.competition_status,
        },
        assignments: [],
      }
    }
    grouped[assignment.competition_id].assignments.push(assignment)
  }

  return Object.values(grouped)
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

    // Load submissions count
    const subsResponse = await apiClient.get('/submissions')
    stats.value.totalSubmissions = subsResponse.data.length
  } catch (err) {
    error.value = 'Failed to load admin data'
    console.error('Failed to load admin data:', err)
  } finally {
    isLoading.value = false
  }
}

const loadJudgesData = async () => {
  try {
    isLoadingJudges.value = true
    error.value = ''

    const [judgesResponse, assignmentsResponse] = await Promise.all([
      apiClient.get('/scores/admin/judges'),
      apiClient.get('/scores/admin/judge-assignments'),
    ])

    judges.value = judgesResponse.data
    judgeAssignments.value = assignmentsResponse.data.filter((a: JudgeAssignment) => a.is_active)
  } catch (err) {
    error.value = 'Failed to load judges data'
    console.error('Failed to load judges:', err)
  } finally {
    isLoadingJudges.value = false
  }
}

const assignJudge = async () => {
  if (!selectedJudgeId.value || !selectedCompetitionId.value) {
    error.value = 'Please select both a judge and a competition'
    return
  }

  try {
    isAssigning.value = true
    error.value = ''
    success.value = ''

    await apiClient.post(`/scores/admin/judge-assignments?judge_id=${selectedJudgeId.value}&competition_id=${selectedCompetitionId.value}`)

    success.value = 'Judge assigned successfully'
    selectedJudgeId.value = null
    selectedCompetitionId.value = null
    await loadJudgesData()
  } catch (err: unknown) {
    if (err && typeof err === 'object' && 'response' in err) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      error.value = axiosErr.response?.data?.detail || 'Failed to assign judge'
    } else {
      error.value = 'Failed to assign judge'
    }
  } finally {
    isAssigning.value = false
  }
}

const removeAssignment = async (assignmentId: number) => {
  try {
    error.value = ''
    success.value = ''

    await apiClient.delete(`/scores/admin/judge-assignments/${assignmentId}`)

    success.value = 'Judge assignment removed'
    await loadJudgesData()
  } catch (err) {
    error.value = 'Failed to remove assignment'
  }
}

const updateUserRole = async (userId: number, newRole: string) => {
  try {
    error.value = ''
    success.value = ''
    await apiClient.patch(`/users/${userId}`, { role: newRole })
    success.value = `User role updated to ${newRole}`
    await loadStats()
  } catch (err) {
    error.value = 'Failed to update user role'
  }
}

const toggleUserStatus = async (userId: number, isActive: boolean) => {
  try {
    error.value = ''
    success.value = ''
    await apiClient.patch(`/users/${userId}`, { is_active: isActive })
    success.value = `User ${isActive ? 'enabled' : 'disabled'} successfully`
    await loadStats()
  } catch (err) {
    error.value = 'Failed to update user status'
  }
}

const handleTabChange = async (tab: 'users' | 'competitions' | 'judges' | 'stats' | 'scoring') => {
  activeTab.value = tab
  searchQuery.value = ''

  if (tab === 'judges' && judges.value.length === 0) {
    await loadJudgesData()
  }

  if (tab === 'scoring' && auditLogs.value.length === 0 && competitions.value.length > 0) {
    // Auto-select first competition with submissions
    selectedAuditCompetitionId.value = competitions.value[0]?.id || null
    if (selectedAuditCompetitionId.value) {
      await loadAuditLogs()
    }
  }
}

const loadAuditLogs = async () => {
  if (!selectedAuditCompetitionId.value) return

  isLoadingAuditLogs.value = true
  try {
    const response = await apiClient.get<AuditLogListResponse>(
      `/scores/audit-logs/competition/${selectedAuditCompetitionId.value}`
    )
    auditLogs.value = response.data.logs
    auditLogStats.value = {
      total_count: response.data.total_count,
      unique_sessions: response.data.unique_sessions,
      unique_ips: response.data.unique_ips,
    }
  } catch (err) {
    console.error('Failed to load audit logs:', err)
    error.value = 'Failed to load scoring activity logs'
  } finally {
    isLoadingAuditLogs.value = false
  }
}

const onCompetitionChange = async () => {
  auditLogs.value = []
  auditLogStats.value = null
  if (selectedAuditCompetitionId.value) {
    await loadAuditLogs()
  }
}

const getActionTypeVariant = (actionType: string) => {
  const variants: Record<string, string> = {
    create: 'success',
    update: 'info',
    delete: 'destructive',
  }
  return variants[actionType] || 'outline'
}

const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

const truncateUserAgent = (ua: string | null) => {
  if (!ua) return 'Unknown'
  if (ua.includes('Chrome')) return 'Chrome'
  if (ua.includes('Firefox')) return 'Firefox'
  if (ua.includes('Safari')) return 'Safari'
  if (ua.includes('Edge')) return 'Edge'
  return ua.length > 30 ? ua.substring(0, 30) + '...' : ua
}

const getRoleVariant = (role: string) => {
  const variants: Record<string, string> = {
    admin: 'destructive',
    organizer: 'default',
    judge: 'secondary',
    participant: 'outline',
  }
  return variants[role] || 'secondary'
}

const getStatusVariant = (status: string) => {
  const variants: Record<string, string> = {
    open: 'success',
    judging: 'info',
    closed: 'warning',
    completed: 'secondary',
    draft: 'outline',
  }
  return variants[status] || 'secondary'
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const statCards = computed(() => [
  { label: 'Total Users', value: stats.value.totalUsers, icon: Users },
  { label: 'Total Competitions', value: stats.value.totalCompetitions, icon: Trophy },
  { label: 'Active Competitions', value: stats.value.activeCompetitions, icon: Activity },
  { label: 'Total Submissions', value: stats.value.totalSubmissions, icon: Image },
])
</script>

<template>
  <div class="container mx-auto px-4 md:px-6 py-6 md:py-10">
    <div class="mb-6 md:mb-8">
      <span class="inline-flex items-center gap-2 rounded-full border bg-card px-3 py-1 text-xs font-medium text-muted-foreground mb-3">
        <span class="h-1.5 w-1.5 rounded-full bg-brand" />
        Platform administration
      </span>
      <h1 class="text-3xl md:text-4xl font-display font-semibold tracking-tight">Admin panel</h1>
      <p class="mt-2 text-muted-foreground">
        Manage users, competitions, judges, and scoring integrity
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

    <Alert v-if="success" class="mb-6 bg-success/10 border-success/30 text-success">
      <AlertDescription>{{ success }}</AlertDescription>
    </Alert>

    <!-- Loading state -->
    <div v-if="isLoading" class="text-center py-20">
      <Loader2 class="w-8 h-8 text-muted-foreground animate-spin mx-auto mb-6" />
      <p class="text-muted-foreground text-lg">Loading admin data...</p>
    </div>

    <template v-else-if="isAdmin">
      <!-- Tab Navigation - Scrollable on mobile -->
      <div class="overflow-x-auto -mx-4 px-4 md:mx-0 md:px-0 mb-6 md:mb-8">
        <div class="inline-flex rounded-full border bg-card p-1 min-w-max">
          <Button
            variant="ghost"
            size="sm"
            :class="[
              'rounded-full transition-all text-sm md:text-base px-3 md:px-4',
              activeTab === 'stats' ? 'bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground' : 'text-muted-foreground hover:bg-accent'
            ]"
            @click="handleTabChange('stats')"
          >
            Dashboard
          </Button>
          <Button
            variant="ghost"
            size="sm"
            :class="[
              'rounded-full transition-all text-sm md:text-base px-3 md:px-4',
              activeTab === 'users' ? 'bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground' : 'text-muted-foreground hover:bg-accent'
            ]"
            @click="handleTabChange('users')"
          >
            Users
          </Button>
          <Button
            variant="ghost"
            size="sm"
            :class="[
              'rounded-full transition-all text-sm md:text-base px-3 md:px-4',
              activeTab === 'competitions' ? 'bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground' : 'text-muted-foreground hover:bg-accent'
            ]"
            @click="handleTabChange('competitions')"
          >
            Competitions
          </Button>
          <Button
            variant="ghost"
            size="sm"
            :class="[
              'rounded-full transition-all text-sm md:text-base px-3 md:px-4',
              activeTab === 'judges' ? 'bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground' : 'text-muted-foreground hover:bg-accent'
            ]"
            @click="handleTabChange('judges')"
          >
            <Gavel class="w-4 h-4 mr-1 md:mr-2" />
            <span class="hidden sm:inline">Judge</span> Assignments
          </Button>
          <Button
            variant="ghost"
            size="sm"
            :class="[
              'rounded-full transition-all text-sm md:text-base px-3 md:px-4',
              activeTab === 'scoring' ? 'bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground' : 'text-muted-foreground hover:bg-accent'
            ]"
            @click="handleTabChange('scoring')"
          >
            <History class="w-4 h-4 mr-1 md:mr-2" />
            <span class="hidden sm:inline">Score</span> Audit
          </Button>
          <Button
            variant="ghost"
            size="sm"
            :class="[
              'rounded-full transition-all text-sm md:text-base px-3 md:px-4',
              activeTab === 'v2analytics' ? 'bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground' : 'text-muted-foreground hover:bg-accent'
            ]"
            @click="handleTabChange('v2analytics')"
          >
            <BarChart3 class="w-4 h-4 mr-1 md:mr-2" />
            Analytics
          </Button>
        </div>
      </div>

      <!-- Stats Tab -->
      <div v-if="activeTab === 'stats'" class="space-y-4 md:space-y-6">
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-6">
          <Card v-for="stat in statCards" :key="stat.label" class="rounded-2xl">
            <CardHeader class="pb-2">
              <div class="flex items-center justify-between">
                <CardDescription>{{ stat.label }}</CardDescription>
                <div class="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center">
                  <component :is="stat.icon" class="w-5 h-5 text-foreground" />
                </div>
              </div>
              <CardTitle class="text-3xl md:text-4xl font-display font-semibold">{{ stat.value }}</CardTitle>
            </CardHeader>
          </Card>
        </div>

        <!-- Quick Actions -->
        <Card class="rounded-2xl">
          <CardHeader>
            <CardTitle>Quick actions</CardTitle>
          </CardHeader>
          <CardContent class="flex gap-4 flex-wrap">
            <Button @click="router.push('/competitions')">
              <Eye class="w-4 h-4 mr-2" />
              View competitions
            </Button>
            <Button variant="outline" @click="loadStats">
              <RefreshCw class="w-4 h-4 mr-2" />
              Refresh stats
            </Button>
            <Button variant="secondary" @click="handleTabChange('judges')">
              <Gavel class="w-4 h-4 mr-2" />
              Manage judges
            </Button>
          </CardContent>
        </Card>
      </div>

      <!-- Users Tab -->
      <div v-if="activeTab === 'users'">
        <!-- Search -->
        <div class="relative mb-6">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <Input
            v-model="searchQuery"
            placeholder="Search users..."
            class="pl-10 h-12 text-base"
          />
          <button
            v-if="searchQuery"
            @click="searchQuery = ''"
            aria-label="Clear search"
            class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          >
            <X class="w-4 h-4" />
          </button>
        </div>

        <Card class="rounded-2xl">
          <CardHeader>
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center">
                <Users class="w-5 h-5 text-foreground" />
              </div>
              <div>
                <CardTitle>User management</CardTitle>
                <CardDescription>{{ filteredUsers.length }} users</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div class="overflow-x-auto rounded-2xl border">
              <table class="w-full text-sm">
                <thead>
                  <tr class="text-xs uppercase tracking-wide text-muted-foreground border-b">
                    <th class="text-left py-3 px-4 font-medium">User</th>
                    <th class="text-left py-3 px-4 font-medium">Role</th>
                    <th class="text-left py-3 px-4 font-medium">Status</th>
                    <th class="text-left py-3 px-4 font-medium">Joined</th>
                    <th class="text-left py-3 px-4 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="user in filteredUsers" :key="user.id" class="border-b last:border-0 hover:bg-muted/50 transition-colors">
                    <td class="py-3 px-4">
                      <div>
                        <p class="font-medium">{{ user.username }}</p>
                        <p class="text-muted-foreground text-xs">{{ user.email }}</p>
                      </div>
                    </td>
                    <td class="py-3 px-4">
                      <Badge :variant="getRoleVariant(user.role)">
                        {{ user.role.toUpperCase() }}
                      </Badge>
                    </td>
                    <td class="py-3 px-4">
                      <Badge :variant="user.is_active ? 'success' : 'destructive'">
                        {{ user.is_active ? 'Active' : 'Inactive' }}
                      </Badge>
                    </td>
                    <td class="py-3 px-4 text-muted-foreground">{{ formatDate(user.created_at) }}</td>
                    <td class="py-3 px-4">
                      <div class="flex gap-2">
                        <select
                          aria-label="Change role"
                          class="h-10 rounded-xl border border-input bg-card px-3 py-2 text-sm cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
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
                          :variant="user.is_active ? 'outline' : 'default'"
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
        <!-- Search -->
        <div class="relative mb-6">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <Input
            v-model="searchQuery"
            placeholder="Search competitions..."
            class="pl-10 h-12 text-base"
          />
          <button
            v-if="searchQuery"
            @click="searchQuery = ''"
            aria-label="Clear search"
            class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          >
            <X class="w-4 h-4" />
          </button>
        </div>

        <Card class="rounded-2xl">
          <CardHeader>
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center">
                <Trophy class="w-5 h-5 text-foreground" />
              </div>
              <div>
                <CardTitle>Competition management</CardTitle>
                <CardDescription>{{ filteredCompetitions.length }} competitions</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div class="overflow-x-auto rounded-2xl border">
              <table class="w-full text-sm">
                <thead>
                  <tr class="text-xs uppercase tracking-wide text-muted-foreground border-b">
                    <th class="text-left py-3 px-4 font-medium">Competition</th>
                    <th class="text-left py-3 px-4 font-medium">Status</th>
                    <th class="text-left py-3 px-4 font-medium">Dates</th>
                    <th class="text-left py-3 px-4 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="comp in filteredCompetitions" :key="comp.id" class="border-b last:border-0 hover:bg-muted/50 transition-colors">
                    <td class="py-3 px-4">
                      <p class="font-medium">{{ comp.title }}</p>
                    </td>
                    <td class="py-3 px-4">
                      <Badge :variant="getStatusVariant(comp.status)">
                        {{ comp.status.toUpperCase() }}
                      </Badge>
                    </td>
                    <td class="py-3 px-4 text-muted-foreground">
                      <div class="flex items-center gap-1">
                        <Calendar class="w-3 h-3" />
                        {{ formatDate(comp.submission_start) }} - {{ formatDate(comp.submission_end) }}
                      </div>
                    </td>
                    <td class="py-3 px-4">
                      <Button
                        size="sm"
                        variant="outline"
                        @click="router.push(`/competitions/${comp.id}`)"
                      >
                        <Eye class="w-3 h-3 mr-1" />
                        View
                      </Button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- Judges Tab -->
      <div v-if="activeTab === 'judges'">
        <!-- Loading -->
        <div v-if="isLoadingJudges" class="text-center py-12">
          <Loader2 class="w-8 h-8 text-muted-foreground animate-spin mx-auto mb-4" />
          <p class="text-muted-foreground">Loading judge data...</p>
        </div>

        <template v-else>
          <!-- Assign Judge Card -->
          <Card class="mb-6 rounded-2xl">
            <CardHeader>
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-success/10 flex items-center justify-center">
                  <UserPlus class="w-5 h-5 text-success" />
                </div>
                <div>
                  <CardTitle>Assign judge to competition</CardTitle>
                  <CardDescription>Select a judge and competition to create an assignment</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div class="flex flex-wrap gap-4 items-end">
                <div class="flex-1 min-w-[200px]">
                  <Label class="mb-2 block">Select judge</Label>
                  <select
                    v-model="selectedJudgeId"
                    class="h-10 w-full rounded-xl border border-input bg-card px-3 py-2 text-sm cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <option :value="null">-- Choose a judge --</option>
                    <option v-for="judge in judges" :key="judge.id" :value="judge.id">
                      {{ judge.username }} ({{ judge.email }})
                    </option>
                  </select>
                </div>

                <div class="flex-1 min-w-[200px]">
                  <Label class="mb-2 block">Select competition</Label>
                  <select
                    v-model="selectedCompetitionId"
                    class="h-10 w-full rounded-xl border border-input bg-card px-3 py-2 text-sm cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <option :value="null">-- Choose a competition --</option>
                    <option v-for="comp in competitions" :key="comp.id" :value="comp.id">
                      {{ comp.title }} ({{ comp.status }})
                    </option>
                  </select>
                </div>

                <Button @click="assignJudge" :disabled="isAssigning || !selectedJudgeId || !selectedCompetitionId">
                  <Loader2 v-if="isAssigning" class="w-4 h-4 mr-2 animate-spin" />
                  <Plus v-else class="w-4 h-4 mr-2" />
                  Assign judge
                </Button>
              </div>

              <p v-if="judges.length === 0" class="mt-4 text-sm text-muted-foreground">
                No judges found. Change a user's role to "Judge" in the Users tab first.
              </p>
            </CardContent>
          </Card>

          <!-- Current Assignments -->
          <Card class="rounded-2xl">
            <CardHeader>
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center">
                  <Gavel class="w-5 h-5 text-foreground" />
                </div>
                <div>
                  <CardTitle>Current judge assignments</CardTitle>
                  <CardDescription>
                    {{ judgeAssignments.length }} active assignments across {{ assignmentsByCompetition.length }} competitions
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div v-if="assignmentsByCompetition.length === 0" class="text-center py-8 text-muted-foreground">
                No judge assignments yet. Use the form above to assign judges to competitions.
              </div>

              <div v-else class="space-y-6">
                <div
                  v-for="group in assignmentsByCompetition"
                  :key="group.competition.id"
                  class="p-4 rounded-2xl border bg-muted/20"
                >
                  <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center gap-3">
                      <Trophy class="w-5 h-5 text-foreground" />
                      <div>
                        <h3 class="font-semibold">{{ group.competition.title }}</h3>
                        <Badge :variant="getStatusVariant(group.competition.status)" class="text-xs">
                          {{ group.competition.status.toUpperCase() }}
                        </Badge>
                      </div>
                    </div>
                    <span class="text-sm text-muted-foreground">
                      {{ group.assignments.length }} judge(s)
                    </span>
                  </div>

                  <div class="grid sm:grid-cols-2 md:grid-cols-3 gap-3">
                    <div
                      v-for="assignment in group.assignments"
                      :key="assignment.id"
                      class="flex items-center justify-between p-3 rounded-2xl bg-card border"
                    >
                      <div class="flex items-center gap-2">
                        <div class="w-8 h-8 rounded-full bg-secondary text-foreground flex items-center justify-center">
                          <span class="text-sm font-medium">{{ assignment.judge_username.charAt(0).toUpperCase() }}</span>
                        </div>
                        <div>
                          <p class="text-sm font-medium">{{ assignment.judge_username }}</p>
                          <p class="text-xs text-muted-foreground">{{ assignment.judge_email }}</p>
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        aria-label="Remove judge assignment"
                        class="text-destructive hover:text-destructive hover:bg-destructive/10"
                        @click="removeAssignment(assignment.id)"
                      >
                        <Trash2 class="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </template>
      </div>

      <!-- Score Audit Logs Tab -->
      <div v-if="activeTab === 'scoring'">
        <!-- Competition Selector -->
        <Card class="mb-6 rounded-2xl">
          <CardHeader>
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center">
                <History class="w-5 h-5 text-foreground" />
              </div>
              <div>
                <CardTitle>Score audit logs</CardTitle>
                <CardDescription>View all scoring activity with judge details, IP addresses, and timestamps</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div class="flex flex-col sm:flex-row sm:items-end gap-3 md:gap-4">
              <div class="flex-1">
                <Label class="mb-2 block text-sm">Select competition</Label>
                <select
                  v-model="selectedAuditCompetitionId"
                  @change="onCompetitionChange"
                  class="h-10 w-full rounded-xl border border-input bg-card px-3 py-2 text-sm cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option :value="null">-- Choose a competition --</option>
                  <option v-for="comp in competitions" :key="comp.id" :value="comp.id">
                    {{ comp.title }} ({{ comp.status }})
                  </option>
                </select>
              </div>
              <Button variant="outline" size="sm" class="w-full sm:w-auto" @click="loadAuditLogs" :disabled="isLoadingAuditLogs || !selectedAuditCompetitionId">
                <RefreshCw class="w-4 h-4 mr-2" :class="{ 'animate-spin': isLoadingAuditLogs }" />
                Refresh
              </Button>
            </div>
          </CardContent>
        </Card>

        <!-- Audit Stats Summary -->
        <div v-if="auditLogStats && selectedAuditCompetitionId" class="grid grid-cols-1 sm:grid-cols-3 gap-3 md:gap-4 mb-6">
          <Card class="rounded-2xl">
            <CardContent class="pt-4 md:pt-6 text-center">
              <p class="text-2xl md:text-3xl font-display font-semibold">{{ auditLogStats.total_count }}</p>
              <p class="text-xs md:text-sm text-muted-foreground">Total score actions</p>
            </CardContent>
          </Card>
          <Card class="rounded-2xl">
            <CardContent class="pt-4 md:pt-6 text-center">
              <p class="text-2xl md:text-3xl font-display font-semibold">{{ auditLogStats.unique_ips }}</p>
              <p class="text-xs md:text-sm text-muted-foreground flex items-center justify-center gap-1">
                <Network class="w-3 h-3" /> Unique IP addresses
              </p>
            </CardContent>
          </Card>
          <Card class="rounded-2xl">
            <CardContent class="pt-4 md:pt-6 text-center">
              <p class="text-2xl md:text-3xl font-display font-semibold">{{ auditLogStats.unique_sessions }}</p>
              <p class="text-xs md:text-sm text-muted-foreground flex items-center justify-center gap-1">
                <Monitor class="w-3 h-3" /> Unique sessions
              </p>
            </CardContent>
          </Card>
        </div>

        <!-- Loading State -->
        <div v-if="isLoadingAuditLogs" class="text-center py-12">
          <Loader2 class="w-8 h-8 text-muted-foreground animate-spin mx-auto mb-4" />
          <p class="text-muted-foreground">Loading scoring activity...</p>
        </div>

        <!-- No Competition Selected -->
        <div v-else-if="!selectedAuditCompetitionId" class="text-center py-12">
          <div class="w-16 h-16 rounded-full bg-secondary flex items-center justify-center mx-auto mb-4">
            <History class="w-8 h-8 text-muted-foreground" />
          </div>
          <p class="text-lg text-muted-foreground">Select a competition to view scoring activity</p>
        </div>

        <!-- No Logs -->
        <div v-else-if="auditLogs.length === 0" class="text-center py-12">
          <div class="w-16 h-16 rounded-full bg-secondary flex items-center justify-center mx-auto mb-4">
            <History class="w-8 h-8 text-muted-foreground" />
          </div>
          <p class="text-lg text-muted-foreground">No scoring activity recorded for this competition yet.</p>
        </div>

        <!-- Audit Logs Table -->
        <Card v-else class="rounded-2xl">
          <CardHeader>
            <CardTitle>Scoring activity ({{ auditLogs.length }} actions)</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="overflow-x-auto rounded-2xl border">
              <table class="w-full text-sm">
                <thead>
                  <tr class="text-xs uppercase tracking-wide text-muted-foreground border-b">
                    <th class="text-left py-3 px-4 font-medium">Action</th>
                    <th class="text-left py-3 px-4 font-medium">Submission</th>
                    <th class="text-left py-3 px-4 font-medium">Scores</th>
                    <th class="text-left py-3 px-4 font-medium">Judge Info</th>
                    <th class="text-left py-3 px-4 font-medium">Client Details</th>
                    <th class="text-left py-3 px-4 font-medium">Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="log in auditLogs" :key="log.id" class="border-b last:border-0 hover:bg-muted/50 transition-colors">
                    <td class="py-3 px-4">
                      <Badge :variant="getActionTypeVariant(log.action_type)">
                        {{ log.action_type.toUpperCase() }}
                      </Badge>
                    </td>
                    <td class="py-3 px-4">
                      <span class="font-mono text-muted-foreground">#{{ log.submission_id }}</span>
                    </td>
                    <td class="py-3 px-4">
                      <div v-if="log.action_type !== 'delete'" class="text-xs space-y-1">
                        <div class="flex gap-3">
                          <span>C: <strong>{{ log.composition_score?.toFixed(1) }}</strong></span>
                          <span>T: <strong>{{ log.technical_score?.toFixed(1) }}</strong></span>
                          <span>R: <strong>{{ log.creativity_score?.toFixed(1) }}</strong></span>
                        </div>
                        <div class="font-bold text-primary">
                          Overall: {{ log.overall_score?.toFixed(2) }}
                        </div>
                      </div>
                      <div v-else class="text-xs text-muted-foreground">
                        Deleted score
                      </div>
                    </td>
                    <td class="py-3 px-4">
                      <div class="text-xs">
                        <div class="font-medium">Judge ID: {{ log.judge_id }}</div>
                        <div v-if="log.judge_identifier" class="text-primary font-semibold">
                          <UserIcon class="w-3 h-3 inline mr-1" />
                          {{ log.judge_identifier }}
                        </div>
                      </div>
                    </td>
                    <td class="py-3 px-4">
                      <div class="text-xs space-y-1">
                        <div class="flex items-center gap-1">
                          <Network class="w-3 h-3 text-muted-foreground" />
                          <span class="font-mono">{{ log.ip_address || 'Unknown' }}</span>
                        </div>
                        <div class="flex items-center gap-1">
                          <Monitor class="w-3 h-3 text-muted-foreground" />
                          <span>{{ truncateUserAgent(log.user_agent) }}</span>
                        </div>
                      </div>
                    </td>
                    <td class="py-3 px-4 text-xs text-muted-foreground whitespace-nowrap">
                      {{ formatDateTime(log.created_at) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- V2 Analytics Tab -->
      <div v-if="activeTab === 'v2analytics'" class="space-y-4 md:space-y-6">
        <Card class="rounded-2xl">
          <CardHeader>
            <div class="flex items-center justify-between">
              <div>
                <CardTitle class="flex items-center gap-2">
                  <BarChart3 class="w-5 h-5" />
                  Advanced analytics
                </CardTitle>
                <CardDescription>
                  Camera reputation, judge bias analysis, and credential sharing detection
                </CardDescription>
              </div>
            </div>
          </CardHeader>
        </Card>

        <!-- Camera Reputation Statistics -->
        <Card class="rounded-2xl">
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <Shield class="w-5 h-5" />
              Camera reputation system
            </CardTitle>
            <CardDescription>PRNU fingerprinting and trust scoring</CardDescription>
          </CardHeader>
          <CardContent>
            <div class="space-y-4">
              <Alert>
                <Activity class="h-4 w-4" />
                <AlertDescription>
                  Camera reputation system tracks PRNU (Photo Response Non-Uniformity) fingerprints to verify photo authenticity and build trust profiles for camera models.
                </AlertDescription>
              </Alert>

              <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card class="rounded-2xl">
                  <CardContent class="pt-6 text-center">
                    <p class="text-3xl font-display font-semibold text-muted-foreground">Coming soon</p>
                    <p class="text-sm text-muted-foreground mt-2">Camera profiles</p>
                  </CardContent>
                </Card>
                <Card class="rounded-2xl">
                  <CardContent class="pt-6 text-center">
                    <p class="text-3xl font-display font-semibold text-muted-foreground">Active</p>
                    <p class="text-sm text-muted-foreground mt-2">PRNU extraction</p>
                  </CardContent>
                </Card>
                <Card class="rounded-2xl">
                  <CardContent class="pt-6 text-center">
                    <p class="text-3xl font-display font-semibold text-muted-foreground">Ready</p>
                    <p class="text-sm text-muted-foreground mt-2">Fraud detection</p>
                  </CardContent>
                </Card>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Judge Bias Analysis Dashboard -->
        <BiasReportDashboard
          v-if="competitions.length > 0"
          :competition-id="competitions[0]?.id"
        />

        <!-- Credential Sharing Alerts -->
        <Card class="rounded-2xl">
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <Shield class="w-5 h-5" />
              Credential sharing detection
            </CardTitle>
            <CardDescription>Monitor for suspicious judge account activity</CardDescription>
          </CardHeader>
          <CardContent>
            <Alert>
              <Activity class="h-4 w-4" />
              <AlertDescription>
                The system monitors IP addresses, session patterns, and user agents to detect potential credential sharing among judges.
                Real-time alerts will appear here when suspicious activity is detected.
              </AlertDescription>
            </Alert>

            <div v-if="v2Analytics.isLoading" class="text-center py-8">
              <Loader2 class="w-8 h-8 animate-spin mx-auto text-muted-foreground" />
              <p class="text-sm text-muted-foreground mt-2">Checking for alerts...</p>
            </div>

            <div v-else class="mt-4">
              <p class="text-sm text-muted-foreground text-center py-8">
                No credential sharing alerts at this time. The system is actively monitoring all judge activities.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </template>
  </div>
</template>
