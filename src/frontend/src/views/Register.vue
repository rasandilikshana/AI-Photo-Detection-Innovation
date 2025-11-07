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
  <div class="min-h-screen flex items-center justify-center bg-muted/50 px-4 py-8">
    <Card class="w-full max-w-md">
      <CardHeader>
        <CardTitle class="text-2xl">Create Account</CardTitle>
        <CardDescription>Join A.V.A.R. and participate in photography competitions</CardDescription>
      </CardHeader>
      <CardContent class="space-y-4">
        <Alert v-if="authStore.error" variant="destructive">
          <AlertDescription>{{ authStore.error }}</AlertDescription>
        </Alert>

        <form @submit.prevent="handleRegister" class="space-y-4">
          <div class="space-y-2">
            <Label for="email">Email*</Label>
            <Input
              id="email"
              v-model="formData.email"
              type="email"
              placeholder="you@example.com"
              required
              :disabled="isLoading"
            />
          </div>

          <div class="space-y-2">
            <Label for="username">Username*</Label>
            <Input
              id="username"
              v-model="formData.username"
              type="text"
              placeholder="photographer123"
              required
              :disabled="isLoading"
            />
          </div>

          <div class="space-y-2">
            <Label for="full_name">Full Name</Label>
            <Input
              id="full_name"
              v-model="formData.full_name"
              type="text"
              placeholder="John Doe"
              :disabled="isLoading"
            />
          </div>

          <div class="space-y-2">
            <Label for="country">Country</Label>
            <Input
              id="country"
              v-model="formData.country"
              type="text"
              placeholder="United States"
              :disabled="isLoading"
            />
          </div>

          <div class="space-y-2">
            <Label for="password">Password*</Label>
            <Input
              id="password"
              v-model="formData.password"
              type="password"
              placeholder="••••••••"
              required
              :disabled="isLoading"
            />
          </div>

          <div class="space-y-2">
            <Label for="confirmPassword">Confirm Password*</Label>
            <Input
              id="confirmPassword"
              v-model="formData.confirmPassword"
              type="password"
              placeholder="••••••••"
              required
              :disabled="isLoading"
            />
          </div>

          <Button type="submit" class="w-full" :disabled="isLoading">
            {{ isLoading ? 'Creating account...' : 'Create Account' }}
          </Button>
        </form>
      </CardContent>
      <CardFooter class="flex justify-center">
        <p class="text-sm text-muted-foreground">
          Already have an account?
          <router-link to="/login" class="text-primary hover:underline font-medium">
            Sign in
          </router-link>
        </p>
      </CardFooter>
    </Card>
  </div>
</template>
