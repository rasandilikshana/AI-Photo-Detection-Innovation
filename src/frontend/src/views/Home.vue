<template>
  <div class="home-page">
    <!-- Hero Section -->
    <section class="hero-section">
      <v-container>
        <v-row align="center" justify="center" class="fill-height">
          <v-col cols="12" md="6" class="text-center text-md-left">
            <h1 class="text-h2 text-md-h1 font-weight-bold mb-4">
              {{ appTitle }}
            </h1>
            <p class="text-h6 text-md-h5 text-medium-emphasis mb-8">
              Ensuring authenticity in photography competitions through cutting-edge AI detection technology
            </p>
            <div class="d-flex flex-column flex-sm-row justify-center justify-md-start gap-4">
              <v-btn
                :to="{ name: 'competitions' }"
                color="primary"
                size="x-large"
                elevation="2"
              >
                <v-icon start>mdi-trophy</v-icon>
                Browse Competitions
              </v-btn>
              <v-btn
                v-if="!authStore.isAuthenticated"
                :to="{ name: 'register' }"
                color="accent"
                size="x-large"
                elevation="2"
              >
                <v-icon start>mdi-account-plus</v-icon>
                Get Started
              </v-btn>
            </div>
          </v-col>
          <v-col cols="12" md="6" class="d-none d-md-block">
            <v-img
              src="https://images.unsplash.com/photo-1542038784456-1ea8e935640e?w=800"
              alt="Photography"
              cover
              class="rounded-lg elevation-8"
              aspect-ratio="1.5"
            />
          </v-col>
        </v-row>
      </v-container>
    </section>

    <!-- Features Section -->
    <section class="features-section py-16">
      <v-container>
        <h2 class="text-h3 font-weight-bold text-center mb-4">Why Choose {{ appName }}?</h2>
        <p class="text-h6 text-center text-medium-emphasis mb-12">
          The most trusted platform for authentic photography competitions
        </p>

        <v-row>
          <v-col
            v-for="feature in features"
            :key="feature.title"
            cols="12"
            md="4"
          >
            <v-card class="h-100" elevation="2" hover>
              <v-card-text class="text-center pa-8">
                <v-avatar :color="feature.color" size="80" class="mb-4">
                  <v-icon size="48" color="white">{{ feature.icon }}</v-icon>
                </v-avatar>
                <h3 class="text-h5 font-weight-bold mb-3">{{ feature.title }}</h3>
                <p class="text-body-1 text-medium-emphasis">{{ feature.description }}</p>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </section>

    <!-- How It Works Section -->
    <section class="how-it-works-section py-16 bg-surface">
      <v-container>
        <h2 class="text-h3 font-weight-bold text-center mb-12">How It Works</h2>

        <v-row>
          <v-col
            v-for="(step, index) in steps"
            :key="step.title"
            cols="12"
            md="3"
          >
            <div class="text-center">
              <v-avatar :color="step.color" size="64" class="mb-4">
                <span class="text-h4 font-weight-bold text-white">{{ index + 1 }}</span>
              </v-avatar>
              <h3 class="text-h6 font-weight-bold mb-2">{{ step.title }}</h3>
              <p class="text-body-2 text-medium-emphasis">{{ step.description }}</p>
            </div>
            <v-icon
              v-if="index < steps.length - 1"
              class="d-none d-md-block mt-n12"
              size="32"
              color="primary"
            >
              mdi-arrow-right
            </v-icon>
          </v-col>
        </v-row>
      </v-container>
    </section>

    <!-- Stats Section -->
    <section class="stats-section py-16">
      <v-container>
        <v-row>
          <v-col
            v-for="stat in stats"
            :key="stat.label"
            cols="12"
            sm="6"
            md="3"
          >
            <div class="text-center">
              <h3 class="text-h3 font-weight-bold text-primary mb-2">{{ stat.value }}</h3>
              <p class="text-h6 text-medium-emphasis">{{ stat.label }}</p>
            </div>
          </v-col>
        </v-row>
      </v-container>
    </section>

    <!-- CTA Section -->
    <section class="cta-section py-16 bg-primary">
      <v-container>
        <v-row align="center" justify="center">
          <v-col cols="12" md="8" class="text-center">
            <h2 class="text-h3 font-weight-bold text-white mb-4">
              Ready to Join the Community?
            </h2>
            <p class="text-h6 text-white mb-8 text-opacity-90">
              Start participating in authentic photography competitions today
            </p>
            <v-btn
              v-if="!authStore.isAuthenticated"
              :to="{ name: 'register' }"
              color="white"
              size="x-large"
              elevation="2"
            >
              <v-icon start>mdi-account-plus</v-icon>
              Create Free Account
            </v-btn>
            <v-btn
              v-else
              :to="{ name: 'competitions' }"
              color="white"
              size="x-large"
              elevation="2"
            >
              <v-icon start>mdi-trophy</v-icon>
              View Competitions
            </v-btn>
          </v-col>
        </v-row>
      </v-container>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/store/auth'

const authStore = useAuthStore()

const appName = import.meta.env.VITE_APP_NAME || 'A.V.A.R'
const appTitle = import.meta.env.VITE_APP_TITLE || 'Authentic Visual Art Recognition Platform'

const features = [
  {
    icon: 'mdi-shield-check',
    color: 'primary',
    title: 'AI-Powered Detection',
    description:
      'State-of-the-art algorithms detect AI-generated images with high accuracy, ensuring only authentic photographs compete.',
  },
  {
    icon: 'mdi-trophy',
    color: 'success',
    title: 'Fair Competition',
    description:
      'Transparent judging process with role-based access control ensures integrity and fairness for all participants.',
  },
  {
    icon: 'mdi-account-group',
    color: 'info',
    title: 'Global Community',
    description:
      'Join photographers worldwide in a trusted environment where authenticity and creativity are celebrated.',
  },
]

const steps = [
  {
    title: 'Create Account',
    description: 'Sign up for free and complete your photographer profile',
    color: 'primary',
  },
  {
    title: 'Browse Competitions',
    description: 'Find competitions that match your interests and skill level',
    color: 'secondary',
  },
  {
    title: 'Submit Photos',
    description: 'Upload your authentic photographs with metadata and details',
    color: 'accent',
  },
  {
    title: 'Win Prizes',
    description: 'Get judged fairly and win exciting prizes for your work',
    color: 'success',
  },
]

const stats = [
  { value: '10K+', label: 'Active Users' },
  { value: '500+', label: 'Competitions' },
  { value: '50K+', label: 'Submissions' },
  { value: '99.9%', label: 'Detection Accuracy' },
]
</script>

<style scoped>
.home-page {
  min-height: 100vh;
}

.hero-section {
  min-height: 80vh;
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.features-section {
  background: white;
}

.bg-surface {
  background-color: rgb(var(--v-theme-surface));
}

.bg-primary {
  background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
}

.gap-4 {
  gap: 1rem;
}
</style>
