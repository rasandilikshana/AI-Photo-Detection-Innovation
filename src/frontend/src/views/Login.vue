<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'

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
  <div class="min-h-[calc(100vh-10rem)] flex items-center justify-center px-6">
    <Card class="w-full max-w-md">
      <CardHeader class="text-center p-8 pb-6">
        <router-link to="/" class="text-2xl font-bold text-primary mb-3 hover:opacity-80 transition-opacity">A.V.A.R.</router-link>
        <CardTitle class="text-2xl">Sign In</CardTitle>
        <CardDescription class="text-base mt-2">Enter your credentials to continue</CardDescription>
      </CardHeader>
      <CardContent class="space-y-6 px-8">
        <Alert v-if="authStore.error" variant="destructive">
          <AlertDescription class="text-base">{{ authStore.error }}</AlertDescription>
        </Alert>

        <form @submit.prevent="handleLogin" class="space-y-5">
          <div class="space-y-2">
            <Label for="email" class="text-base">Email</Label>
            <Input
              id="email"
              v-model="email"
              type="email"
              placeholder="you@example.com"
              required
              :disabled="isLoading"
              class="h-12 text-base"
            />
          </div>

          <div class="space-y-2">
            <Label for="password" class="text-base">Password</Label>
            <Input
              id="password"
              v-model="password"
              type="password"
              placeholder="••••••••"
              required
              :disabled="isLoading"
              class="h-12 text-base"
            />
          </div>

          <Button type="submit" class="w-full h-12 text-base" :disabled="isLoading">
            {{ isLoading ? 'Signing in...' : 'Sign In' }}
          </Button>
        </form>
      </CardContent>
      <CardFooter class="flex justify-center p-8 pt-4">
        <p class="text-base text-muted-foreground">
          Don't have an account?
          <router-link to="/register" class="text-primary hover:underline font-medium ml-1">
            Sign up
          </router-link>
        </p>
      </CardFooter>
    </Card>
  </div>
</template>
