<template>
  <div class="login-page">
    <h1 class="text-h4 font-weight-bold text-center mb-2">Welcome Back</h1>
    <p class="text-body-1 text-center text-medium-emphasis mb-8">
      Sign in to continue to your account
    </p>

    <!-- Error Message -->
    <ErrorMessage
      v-if="authStore.error"
      :message="authStore.error"
      @close="authStore.clearError()"
    />

    <!-- Login Form -->
    <v-form @submit.prevent="handleSubmit">
      <v-text-field
        v-model="email"
        label="Email"
        type="email"
        prepend-inner-icon="mdi-email"
        :error-messages="emailError"
        :disabled="authStore.loading"
        variant="outlined"
        class="mb-3"
        @blur="validateEmail"
      />

      <v-text-field
        v-model="password"
        label="Password"
        :type="showPassword ? 'text' : 'password'"
        prepend-inner-icon="mdi-lock"
        :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
        :error-messages="passwordError"
        :disabled="authStore.loading"
        variant="outlined"
        class="mb-3"
        @blur="validatePassword"
        @click:append-inner="showPassword = !showPassword"
      />

      <div class="d-flex justify-space-between align-center mb-6">
        <v-checkbox
          v-model="rememberMe"
          label="Remember me"
          density="compact"
          hide-details
        />
        <router-link
          to="/auth/forgot-password"
          class="text-primary text-decoration-none"
        >
          Forgot password?
        </router-link>
      </div>

      <v-btn
        type="submit"
        color="primary"
        size="large"
        block
        :loading="authStore.loading"
        :disabled="!isFormValid || authStore.loading"
      >
        Sign In
      </v-btn>
    </v-form>

    <!-- Divider -->
    <v-divider class="my-6" />

    <!-- Register Link -->
    <p class="text-center text-body-2">
      Don't have an account?
      <router-link
        :to="{ name: 'register' }"
        class="text-primary text-decoration-none font-weight-medium"
      >
        Sign Up
      </router-link>
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { useToast } from 'vue-toastification'
import ErrorMessage from '@/components/common/ErrorMessage.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const toast = useToast()

// Form data
const email = ref('')
const password = ref('')
const rememberMe = ref(false)
const showPassword = ref(false)

// Validation errors
const emailError = ref('')
const passwordError = ref('')

// Computed
const isFormValid = computed(() => {
  return email.value && password.value && !emailError.value && !passwordError.value
})

// Validation functions
function validateEmail() {
  if (!email.value) {
    emailError.value = 'Email is required'
    return false
  }
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email.value)) {
    emailError.value = 'Please enter a valid email'
    return false
  }
  emailError.value = ''
  return true
}

function validatePassword() {
  if (!password.value) {
    passwordError.value = 'Password is required'
    return false
  }
  if (password.value.length < 6) {
    passwordError.value = 'Password must be at least 6 characters'
    return false
  }
  passwordError.value = ''
  return true
}

// Form submission
async function handleSubmit() {
  // Validate all fields
  const isEmailValid = validateEmail()
  const isPasswordValid = validatePassword()

  if (!isEmailValid || !isPasswordValid) {
    return
  }

  try {
    await authStore.login({
      email: email.value,
      password: password.value,
    })

    toast.success('Logged in successfully!')

    // Redirect to intended page or dashboard
    const redirectPath = (route.query.redirect as string) || '/dashboard/participant'
    router.push(redirectPath)
  } catch (error) {
    // Error is already handled by the store
    console.error('Login error:', error)
  }
}
</script>

<style scoped>
.login-page {
  width: 100%;
}
</style>
