<template>
  <v-container class="py-8">
    <v-row>
      <v-col cols="12">
        <h1 class="text-h3 font-weight-bold mb-2">My Profile</h1>
        <p class="text-body-1 text-medium-emphasis mb-8">
          Manage your account settings and preferences
        </p>
      </v-col>
    </v-row>

    <v-row>
      <!-- Profile Card -->
      <v-col cols="12" md="4">
        <v-card elevation="2">
          <v-card-text class="text-center pa-8">
            <v-avatar :size="120" class="mb-4">
              <v-img :src="userAvatar" alt="Profile" />
            </v-avatar>

            <h2 class="text-h5 font-weight-bold mb-2">
              {{ authStore.user?.full_name || authStore.user?.username }}
            </h2>

            <v-chip :color="roleColor" class="mb-4" variant="flat">
              {{ authStore.user?.role }}
            </v-chip>

            <v-list density="compact" class="bg-transparent">
              <v-list-item>
                <template #prepend>
                  <v-icon>mdi-email</v-icon>
                </template>
                <v-list-item-title class="text-body-2">
                  {{ authStore.user?.email }}
                </v-list-item-title>
              </v-list-item>

              <v-list-item>
                <template #prepend>
                  <v-icon>mdi-at</v-icon>
                </template>
                <v-list-item-title class="text-body-2">
                  @{{ authStore.user?.username }}
                </v-list-item-title>
              </v-list-item>

              <v-list-item>
                <template #prepend>
                  <v-icon>mdi-calendar</v-icon>
                </template>
                <v-list-item-title class="text-body-2">
                  Joined {{ joinDate }}
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Profile Information Form -->
      <v-col cols="12" md="8">
        <v-card elevation="2">
          <v-card-title class="text-h6 font-weight-bold">
            Personal Information
          </v-card-title>
          <v-divider />

          <v-card-text class="pa-6">
            <v-form>
              <v-row>
                <v-col cols="12">
                  <v-text-field
                    v-model="profile.fullName"
                    label="Full Name"
                    prepend-inner-icon="mdi-account"
                    variant="outlined"
                    :disabled="!editing"
                  />
                </v-col>

                <v-col cols="12">
                  <v-text-field
                    v-model="profile.username"
                    label="Username"
                    prepend-inner-icon="mdi-at"
                    variant="outlined"
                    :disabled="!editing"
                  />
                </v-col>

                <v-col cols="12">
                  <v-text-field
                    v-model="profile.email"
                    label="Email"
                    type="email"
                    prepend-inner-icon="mdi-email"
                    variant="outlined"
                    disabled
                  />
                  <p class="text-caption text-medium-emphasis mt-1">
                    Email cannot be changed
                  </p>
                </v-col>

                <v-col cols="12">
                  <v-textarea
                    v-model="profile.bio"
                    label="Bio"
                    prepend-inner-icon="mdi-text"
                    variant="outlined"
                    :disabled="!editing"
                    rows="3"
                  />
                </v-col>
              </v-row>

              <v-divider class="my-6" />

              <div class="d-flex justify-end gap-4">
                <v-btn
                  v-if="!editing"
                  color="primary"
                  variant="flat"
                  @click="editing = true"
                >
                  <v-icon start>mdi-pencil</v-icon>
                  Edit Profile
                </v-btn>

                <template v-else>
                  <v-btn
                    variant="outlined"
                    @click="cancelEdit"
                  >
                    Cancel
                  </v-btn>
                  <v-btn
                    color="primary"
                    variant="flat"
                    :loading="loading"
                    @click="saveProfile"
                  >
                    <v-icon start>mdi-content-save</v-icon>
                    Save Changes
                  </v-btn>
                </template>
              </div>
            </v-form>
          </v-card-text>
        </v-card>

        <!-- Account Status -->
        <v-card elevation="2" class="mt-4">
          <v-card-title class="text-h6 font-weight-bold">
            Account Status
          </v-card-title>
          <v-divider />

          <v-card-text class="pa-6">
            <v-list density="compact">
              <v-list-item>
                <template #prepend>
                  <v-icon :color="authStore.user?.is_active ? 'success' : 'error'">
                    {{ authStore.user?.is_active ? 'mdi-check-circle' : 'mdi-close-circle' }}
                  </v-icon>
                </template>
                <v-list-item-title>
                  Account Status: {{ authStore.user?.is_active ? 'Active' : 'Inactive' }}
                </v-list-item-title>
              </v-list-item>

              <v-list-item>
                <template #prepend>
                  <v-icon :color="authStore.user?.is_verified ? 'success' : 'warning'">
                    {{ authStore.user?.is_verified ? 'mdi-check-circle' : 'mdi-alert-circle' }}
                  </v-icon>
                </template>
                <v-list-item-title>
                  Email Verification: {{ authStore.user?.is_verified ? 'Verified' : 'Not Verified' }}
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/store/auth'
import { useToast } from 'vue-toastification'
import { format } from 'date-fns'

const authStore = useAuthStore()
const toast = useToast()

const editing = ref(false)
const loading = ref(false)

const profile = ref({
  fullName: '',
  username: '',
  email: '',
  bio: '',
})

const userAvatar = computed(() => {
  const username = authStore.user?.username || 'U'
  return `https://ui-avatars.com/api/?name=${username}&background=1976D2&color=fff&size=200`
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

const joinDate = computed(() => {
  if (!authStore.user?.created_at) return 'N/A'
  return format(new Date(authStore.user.created_at), 'MMMM yyyy')
})

onMounted(() => {
  loadProfile()
})

function loadProfile() {
  if (authStore.user) {
    profile.value = {
      fullName: authStore.user.full_name || '',
      username: authStore.user.username || '',
      email: authStore.user.email || '',
      bio: '',
    }
  }
}

function cancelEdit() {
  editing.value = false
  loadProfile()
}

async function saveProfile() {
  loading.value = true

  try {
    // TODO: Implement profile update API call
    await new Promise((resolve) => setTimeout(resolve, 1000))

    toast.success('Profile updated successfully!')
    editing.value = false
  } catch (error) {
    toast.error('Failed to update profile')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.gap-4 {
  gap: 1rem;
}
</style>
