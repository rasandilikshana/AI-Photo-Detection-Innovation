<template>
  <div class="register-page">
    <h1 class="text-h4 font-weight-bold text-center mb-2">Create Account</h1>
    <p class="text-body-1 text-center text-medium-emphasis mb-8">
      Join {{ appName }} and start participating in authentic photography competitions
    </p>

    <!-- Error Message -->
    <ErrorMessage
      v-if="authStore.error"
      :message="authStore.error"
      @close="authStore.clearError()"
    />

    <!-- Register Form -->
    <v-form @submit.prevent="handleSubmit">
      <v-text-field
        v-model="fullName"
        label="Full Name"
        prepend-inner-icon="mdi-account"
        :error-messages="fullNameError"
        :disabled="authStore.loading"
        variant="outlined"
        class="mb-3"
        @blur="validateFullName"
      />

      <v-text-field
        v-model="username"
        label="Username"
        prepend-inner-icon="mdi-at"
        :error-messages="usernameError"
        :disabled="authStore.loading"
        variant="outlined"
        class="mb-3"
        @blur="validateUsername"
      />

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

      <!-- Password Strength Indicator -->
      <div v-if="password" class="mb-4">
        <div class="d-flex align-center mb-1">
          <span class="text-caption text-medium-emphasis mr-2">Password Strength:</span>
          <span
            class="text-caption font-weight-medium"
            :class="`text-${passwordStrength.color}`"
          >
            {{ passwordStrength.text }}
          </span>
        </div>
        <v-progress-linear
          :model-value="passwordStrength.value"
          :color="passwordStrength.color"
          height="4"
          rounded
        />
      </div>

      <v-text-field
        v-model="confirmPassword"
        label="Confirm Password"
        :type="showConfirmPassword ? 'text' : 'password'"
        prepend-inner-icon="mdi-lock-check"
        :append-inner-icon="showConfirmPassword ? 'mdi-eye-off' : 'mdi-eye'"
        :error-messages="confirmPasswordError"
        :disabled="authStore.loading"
        variant="outlined"
        class="mb-3"
        @blur="validateConfirmPassword"
        @click:append-inner="showConfirmPassword = !showConfirmPassword"
      />

      <v-checkbox
        v-model="agreeToTerms"
        :error-messages="termsError"
        :disabled="authStore.loading"
        density="compact"
        class="mb-4"
      >
        <template #label>
          <span class="text-body-2">
            I agree to the
            <router-link to="/terms" target="_blank" class="text-primary">
              Terms of Service
            </router-link>
            and
            <router-link to="/privacy" target="_blank" class="text-primary">
              Privacy Policy
            </router-link>
          </span>
        </template>
      </v-checkbox>

      <v-btn
        type="submit"
        color="primary"
        size="large"
        block
        :loading="authStore.loading"
        :disabled="!isFormValid || authStore.loading"
      >
        Create Account
      </v-btn>
    </v-form>

    <!-- Divider -->
    <v-divider class="my-6" />

    <!-- Login Link -->
    <p class="text-center text-body-2">
      Already have an account?
      <router-link
        :to="{ name: 'login' }"
        class="text-primary text-decoration-none font-weight-medium"
      >
        Sign In
      </router-link>
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { useToast } from 'vue-toastification'
import ErrorMessage from '@/components/common/ErrorMessage.vue'

const router = useRouter()
const authStore = useAuthStore()
const toast = useToast()

const appName = import.meta.env.VITE_APP_NAME || 'A.V.A.R'

// Form data
const fullName = ref('')
const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const agreeToTerms = ref(false)
const showPassword = ref(false)
const showConfirmPassword = ref(false)

// Validation errors
const fullNameError = ref('')
const usernameError = ref('')
const emailError = ref('')
const passwordError = ref('')
const confirmPasswordError = ref('')
const termsError = ref('')

// Password strength
const passwordStrength = computed(() => {
  if (!password.value) return { value: 0, color: 'grey', text: 'None' }

  let strength = 0
  const pw = password.value

  // Length check
  if (pw.length >= 8) strength += 25
  if (pw.length >= 12) strength += 15

  // Character variety
  if (/[a-z]/.test(pw)) strength += 15
  if (/[A-Z]/.test(pw)) strength += 15
  if (/[0-9]/.test(pw)) strength += 15
  if (/[^a-zA-Z0-9]/.test(pw)) strength += 15

  if (strength <= 25) return { value: strength, color: 'error', text: 'Weak' }
  if (strength <= 50) return { value: strength, color: 'warning', text: 'Fair' }
  if (strength <= 75) return { value: strength, color: 'info', text: 'Good' }
  return { value: strength, color: 'success', text: 'Strong' }
})

const isFormValid = computed(() => {
  return (
    fullName.value &&
    username.value &&
    email.value &&
    password.value &&
    confirmPassword.value &&
    agreeToTerms.value &&
    !fullNameError.value &&
    !usernameError.value &&
    !emailError.value &&
    !passwordError.value &&
    !confirmPasswordError.value
  )
})

// Validation functions
function validateFullName() {
  if (!fullName.value) {
    fullNameError.value = 'Full name is required'
    return false
  }
  if (fullName.value.length < 3) {
    fullNameError.value = 'Full name must be at least 3 characters'
    return false
  }
  fullNameError.value = ''
  return true
}

function validateUsername() {
  if (!username.value) {
    usernameError.value = 'Username is required'
    return false
  }
  if (username.value.length < 3) {
    usernameError.value = 'Username must be at least 3 characters'
    return false
  }
  if (!/^[a-zA-Z0-9_]+$/.test(username.value)) {
    usernameError.value = 'Username can only contain letters, numbers, and underscores'
    return false
  }
  usernameError.value = ''
  return true
}

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
  if (password.value.length < 8) {
    passwordError.value = 'Password must be at least 8 characters'
    return false
  }
  passwordError.value = ''

  // Re-validate confirm password if it has a value
  if (confirmPassword.value) {
    validateConfirmPassword()
  }

  return true
}

function validateConfirmPassword() {
  if (!confirmPassword.value) {
    confirmPasswordError.value = 'Please confirm your password'
    return false
  }
  if (confirmPassword.value !== password.value) {
    confirmPasswordError.value = 'Passwords do not match'
    return false
  }
  confirmPasswordError.value = ''
  return true
}

function validateTerms() {
  if (!agreeToTerms.value) {
    termsError.value = 'You must agree to the terms and privacy policy'
    return false
  }
  termsError.value = ''
  return true
}

// Form submission
async function handleSubmit() {
  // Validate all fields
  const isFullNameValid = validateFullName()
  const isUsernameValid = validateUsername()
  const isEmailValid = validateEmail()
  const isPasswordValid = validatePassword()
  const isConfirmPasswordValid = validateConfirmPassword()
  const isTermsValid = validateTerms()

  if (
    !isFullNameValid ||
    !isUsernameValid ||
    !isEmailValid ||
    !isPasswordValid ||
    !isConfirmPasswordValid ||
    !isTermsValid
  ) {
    return
  }

  try {
    await authStore.register({
      email: email.value,
      username: username.value,
      password: password.value,
      full_name: fullName.value,
    })

    toast.success('Account created successfully! Please log in.')
    router.push({ name: 'login' })
  } catch (error) {
    // Error is already handled by the store
    console.error('Registration error:', error)
  }
}
</script>

<style scoped>
.register-page {
  width: 100%;
}
</style>
