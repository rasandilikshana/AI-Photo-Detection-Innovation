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
  <div class="min-h-[calc(100vh-10rem)] flex items-center justify-center px-6 py-10">
    <Card class="w-full max-w-lg">
      <CardHeader class="text-center p-8 pb-6">
        <router-link to="/" class="text-2xl font-bold text-primary mb-3 hover:opacity-80 transition-opacity">A.V.A.R.</router-link>
        <CardTitle class="text-2xl">Create Account</CardTitle>
        <CardDescription class="text-base mt-2">Join and participate in photography competitions</CardDescription>
      </CardHeader>
      <CardContent class="space-y-6 px-8">
        <Alert v-if="authStore.error" variant="destructive">
          <AlertDescription class="text-base">{{ authStore.error }}</AlertDescription>
        </Alert>

        <form @submit.prevent="handleRegister" class="space-y-5">
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <Label for="email" class="text-base">Email*</Label>
              <Input
                id="email"
                v-model="formData.email"
                type="email"
                placeholder="you@example.com"
                required
                :disabled="isLoading"
                class="h-12 text-base"
              />
            </div>

            <div class="space-y-2">
              <Label for="username" class="text-base">Username*</Label>
              <Input
                id="username"
                v-model="formData.username"
                type="text"
                placeholder="photographer123"
                required
                :disabled="isLoading"
                class="h-12 text-base"
              />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <Label for="full_name" class="text-base">Full Name</Label>
              <Input
                id="full_name"
                v-model="formData.full_name"
                type="text"
                placeholder="John Doe"
                :disabled="isLoading"
                class="h-12 text-base"
              />
            </div>

            <div class="space-y-2">
              <Label for="country" class="text-base">Country</Label>
              <Input
                id="country"
                v-model="formData.country"
                type="text"
                placeholder="United States"
                :disabled="isLoading"
                class="h-12 text-base"
              />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <Label for="password" class="text-base">Password*</Label>
              <Input
                id="password"
                v-model="formData.password"
                type="password"
                placeholder="••••••••"
                required
                :disabled="isLoading"
                class="h-12 text-base"
              />
            </div>

            <div class="space-y-2">
              <Label for="confirmPassword" class="text-base">Confirm Password*</Label>
              <Input
                id="confirmPassword"
                v-model="formData.confirmPassword"
                type="password"
                placeholder="••••••••"
                required
                :disabled="isLoading"
                class="h-12 text-base"
              />
            </div>
          </div>

          <Button type="submit" class="w-full h-12 text-base" :disabled="isLoading">
            {{ isLoading ? 'Creating account...' : 'Create Account' }}
          </Button>
        </form>
      </CardContent>
      <CardFooter class="flex justify-center p-8 pt-4">
        <p class="text-base text-muted-foreground">
          Already have an account?
          <router-link to="/login" class="text-primary hover:underline font-medium ml-1">
            Sign in
          </router-link>
        </p>
      </CardFooter>
    </Card>
  </div>
</template>
