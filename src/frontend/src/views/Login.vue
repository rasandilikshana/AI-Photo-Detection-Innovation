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

const email = ref('')
const password = ref('')
const isLoading = ref(false)

const handleLogin = async () => {
  if (!email.value || !password.value) {
    return
  }

  isLoading.value = true
  try {
    await authStore.login({ email: email.value, password: password.value })
    const redirect = router.currentRoute.value.query.redirect as string || '/competitions'
    router.push(redirect)
  } catch (error) {
    console.error('Login failed:', error)
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

    <Card class="relative w-full max-w-md rounded-3xl shadow-lg">
      <CardHeader class="text-center p-8 pb-6">
        <router-link
          to="/"
          class="mx-auto mb-4 inline-flex items-center gap-2 hover:opacity-80 transition-opacity"
          aria-label="A.V.A.R. home"
        >
          <span class="h-2.5 w-2.5 rounded-full bg-brand" aria-hidden="true" />
          <span class="font-display text-2xl font-bold tracking-tight">A.V.A.R.</span>
        </router-link>
        <CardTitle class="font-display text-2xl tracking-tight">Welcome back</CardTitle>
        <CardDescription class="text-base mt-2">Sign in to continue to your competitions</CardDescription>
      </CardHeader>
      <CardContent class="space-y-6 px-8">
        <Alert v-if="authStore.error" variant="destructive">
          <AlertDescription class="text-base">{{ authStore.error }}</AlertDescription>
        </Alert>

        <form @submit.prevent="handleLogin" class="space-y-5">
          <div class="space-y-2">
            <Label for="email">Email</Label>
            <Input
              id="email"
              v-model="email"
              type="email"
              autocomplete="email"
              placeholder="you@example.com"
              required
              :disabled="isLoading"
              class="h-12 text-base rounded-xl"
            />
          </div>

          <div class="space-y-2">
            <Label for="password">Password</Label>
            <Input
              id="password"
              v-model="password"
              type="password"
              autocomplete="current-password"
              placeholder="••••••••"
              required
              :disabled="isLoading"
              class="h-12 text-base rounded-xl"
            />
          </div>

          <Button type="submit" class="w-full h-12 text-base" :disabled="isLoading">
            <Loader2 v-if="isLoading" class="w-4 h-4 animate-spin" />
            {{ isLoading ? 'Signing in...' : 'Sign in' }}
          </Button>
        </form>
      </CardContent>
      <CardFooter class="flex justify-center p-8 pt-4">
        <p class="text-base text-muted-foreground">
          Don't have an account?
          <router-link to="/register" class="text-foreground font-medium underline-offset-4 hover:underline ml-1">
            Create account
          </router-link>
        </p>
      </CardFooter>
    </Card>
  </div>
</template>
