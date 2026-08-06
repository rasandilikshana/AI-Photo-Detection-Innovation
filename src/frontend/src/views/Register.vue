<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2 } from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()

const formData = ref({
  email: '',
  username: '',
  password: '',
  confirmPassword: '',
  full_name: '',
  country: '',
})
const isLoading = ref(false)

const handleRegister = async () => {
  if (formData.value.password !== formData.value.confirmPassword) {
    authStore.error = 'Passwords do not match'
    return
  }

  isLoading.value = true
  try {
    const { confirmPassword, ...registerData } = formData.value
    await authStore.register(registerData)
    router.push('/competitions')
  } catch (error) {
    console.error('Registration failed:', error)
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="relative min-h-screen flex items-center justify-center px-6 py-10 overflow-hidden">
    <div
      aria-hidden="true"
      class="pointer-events-none absolute -top-40 left-1/2 -translate-x-1/2 h-96 w-[42rem] rounded-full bg-brand/10 blur-3xl"
    ></div>

    <Card class="relative w-full max-w-lg rounded-3xl shadow-lg">
      <CardHeader class="text-center p-8 pb-6">
        <router-link
          to="/"
          class="mx-auto mb-4 inline-flex items-center gap-2 hover:opacity-80 transition-opacity"
          aria-label="A.V.A.R. home"
        >
          <span class="h-2.5 w-2.5 rounded-full bg-brand" aria-hidden="true" />
          <span class="font-display text-2xl font-bold tracking-tight">A.V.A.R.</span>
        </router-link>
        <CardTitle class="font-display text-2xl tracking-tight">Create your account</CardTitle>
        <CardDescription class="text-base mt-2">Compete in AI-verified photography competitions</CardDescription>
      </CardHeader>
      <CardContent class="space-y-6 px-8">
        <Alert v-if="authStore.error" variant="destructive">
          <AlertDescription class="text-base">{{ authStore.error }}</AlertDescription>
        </Alert>

        <form @submit.prevent="handleRegister" class="space-y-5">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="space-y-2">
              <Label for="email">Email *</Label>
              <Input
                id="email"
                v-model="formData.email"
                type="email"
                autocomplete="email"
                placeholder="you@example.com"
                required
                :disabled="isLoading"
                class="h-12 text-base rounded-xl"
              />
            </div>

            <div class="space-y-2">
              <Label for="username">Username *</Label>
              <Input
                id="username"
                v-model="formData.username"
                type="text"
                autocomplete="username"
                placeholder="photographer123"
                required
                :disabled="isLoading"
                class="h-12 text-base rounded-xl"
              />
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="space-y-2">
              <Label for="full_name">Full name</Label>
              <Input
                id="full_name"
                v-model="formData.full_name"
                type="text"
                autocomplete="name"
                placeholder="Your name"
                :disabled="isLoading"
                class="h-12 text-base rounded-xl"
              />
            </div>

            <div class="space-y-2">
              <Label for="country">Country</Label>
              <Input
                id="country"
                v-model="formData.country"
                type="text"
                autocomplete="country-name"
                placeholder="Your country"
                :disabled="isLoading"
                class="h-12 text-base rounded-xl"
              />
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="space-y-2">
              <Label for="password">Password *</Label>
              <Input
                id="password"
                v-model="formData.password"
                type="password"
                autocomplete="new-password"
                placeholder="••••••••"
                required
                :disabled="isLoading"
                class="h-12 text-base rounded-xl"
              />
            </div>

            <div class="space-y-2">
              <Label for="confirmPassword">Confirm password *</Label>
              <Input
                id="confirmPassword"
                v-model="formData.confirmPassword"
                type="password"
                autocomplete="new-password"
                placeholder="••••••••"
                required
                :disabled="isLoading"
                class="h-12 text-base rounded-xl"
              />
            </div>
          </div>

          <p class="text-xs text-muted-foreground">* Required fields</p>

          <Button type="submit" class="w-full h-12 text-base" :disabled="isLoading">
            <Loader2 v-if="isLoading" class="w-4 h-4 animate-spin" />
            {{ isLoading ? 'Creating account...' : 'Create account' }}
          </Button>
        </form>
      </CardContent>
      <CardFooter class="flex justify-center p-8 pt-4">
        <p class="text-base text-muted-foreground">
          Already have an account?
          <router-link to="/login" class="text-foreground font-medium underline-offset-4 hover:underline ml-1">
            Sign in
          </router-link>
        </p>
      </CardFooter>
    </Card>
  </div>
</template>
