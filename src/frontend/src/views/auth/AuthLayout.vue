<template>
  <v-app>
    <v-main class="auth-layout">
      <v-container fluid class="fill-height pa-0">
        <v-row no-gutters class="fill-height">
          <!-- Left Side - Branding -->
          <v-col
            cols="12"
            md="6"
            class="d-none d-md-flex auth-brand-section"
          >
            <div class="brand-content">
              <div class="brand-header">
                <v-icon size="64" color="white">mdi-camera-iris</v-icon>
                <div class="text-h3 font-weight-bold text-white mt-4">
                  {{ appName }}
                </div>
                <p class="text-h6 text-white mt-2 font-weight-light">
                  {{ appTitle }}
                </p>
              </div>

              <div class="brand-features mt-12">
                <div
                  v-for="feature in features"
                  :key="feature.title"
                  class="feature-item mb-6"
                >
                  <v-icon size="32" color="white" class="mb-2">{{ feature.icon }}</v-icon>
                  <h3 class="text-h6 text-white font-weight-medium">{{ feature.title }}</h3>
                  <p class="text-body-1 text-white text-opacity-90 mt-1">
                    {{ feature.description }}
                  </p>
                </div>
              </div>
            </div>
          </v-col>

          <!-- Right Side - Auth Form -->
          <v-col
            cols="12"
            md="6"
            class="auth-form-section"
          >
            <div class="form-container">
              <!-- Mobile Logo -->
              <div class="d-md-none text-center mb-8">
                <v-icon size="48" color="primary">mdi-camera-iris</v-icon>
                <h2 class="text-h5 font-weight-bold mt-2">{{ appName }}</h2>
              </div>

              <!-- Router View for Auth Pages -->
              <router-view v-slot="{ Component }">
                <transition name="slide-fade" mode="out-in">
                  <component :is="Component" />
                </transition>
              </router-view>
            </div>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
const appName = import.meta.env.VITE_APP_NAME || 'A.V.A.R'
const appTitle = import.meta.env.VITE_APP_TITLE || 'Authentic Visual Art Recognition Platform'

const features = [
  {
    icon: 'mdi-shield-check',
    title: 'AI-Powered Detection',
    description: 'Advanced algorithms ensure authentic photographs in every competition.',
  },
  {
    icon: 'mdi-trophy',
    title: 'Fair Competitions',
    description: 'Transparent judging process with integrity at its core.',
  },
  {
    icon: 'mdi-account-group',
    title: 'Global Community',
    description: 'Connect with photographers worldwide in a trusted environment.',
  },
]
</script>

<style scoped>
.auth-layout {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.auth-brand-section {
  background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
  padding: 3rem;
  align-items: center;
  justify-content: center;
}

.brand-content {
  max-width: 500px;
  text-align: center;
}

.brand-header {
  animation: fadeInDown 0.8s ease-out;
}

.feature-item {
  animation: fadeInUp 0.8s ease-out;
  animation-fill-mode: both;
}

.feature-item:nth-child(1) {
  animation-delay: 0.2s;
}

.feature-item:nth-child(2) {
  animation-delay: 0.4s;
}

.feature-item:nth-child(3) {
  animation-delay: 0.6s;
}

.auth-form-section {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: white;
}

.form-container {
  width: 100%;
  max-width: 450px;
  animation: fadeIn 0.6s ease-out;
}

/* Transitions */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.3s ease;
}

.slide-fade-enter-from {
  transform: translateX(20px);
  opacity: 0;
}

.slide-fade-leave-to {
  transform: translateX(-20px);
  opacity: 0;
}

/* Animations */
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
