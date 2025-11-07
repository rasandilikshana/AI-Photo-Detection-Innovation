<template>
  <v-footer app color="surface" class="border-t">
    <v-container>
      <v-row>
        <!-- About Section -->
        <v-col cols="12" md="4">
          <div class="d-flex align-center mb-3">
            <v-icon size="28" color="primary" class="mr-2">mdi-camera-iris</v-icon>
            <h3 class="text-h6 font-weight-bold">{{ appName }}</h3>
          </div>
          <p class="text-body-2 text-medium-emphasis">
            {{ appTitle }}
          </p>
          <p class="text-caption text-medium-emphasis">
            Ensuring authenticity in digital photography competitions through AI-powered detection.
          </p>
        </v-col>

        <!-- Quick Links -->
        <v-col cols="12" sm="6" md="3">
          <h4 class="text-subtitle-1 font-weight-bold mb-3">Quick Links</h4>
          <v-list density="compact" color="transparent">
            <v-list-item
              v-for="link in quickLinks"
              :key="link.path"
              :to="link.path"
              class="px-0"
            >
              <v-list-item-title class="text-body-2">
                {{ link.title }}
              </v-list-item-title>
            </v-list-item>
          </v-list>
        </v-col>

        <!-- Resources -->
        <v-col cols="12" sm="6" md="3">
          <h4 class="text-subtitle-1 font-weight-bold mb-3">Resources</h4>
          <v-list density="compact" color="transparent">
            <v-list-item
              v-for="link in resourceLinks"
              :key="link.title"
              :href="link.href"
              target="_blank"
              class="px-0"
            >
              <v-list-item-title class="text-body-2">
                {{ link.title }}
              </v-list-item-title>
            </v-list-item>
          </v-list>
        </v-col>

        <!-- Social & Contact -->
        <v-col cols="12" md="2">
          <h4 class="text-subtitle-1 font-weight-bold mb-3">Connect</h4>
          <div class="d-flex flex-wrap">
            <v-btn
              v-for="social in socialLinks"
              :key="social.name"
              :icon="social.icon"
              :href="social.href"
              target="_blank"
              variant="text"
              size="small"
              class="mr-1 mb-1"
            />
          </div>
        </v-col>
      </v-row>

      <v-divider class="my-4" />

      <!-- Copyright -->
      <v-row>
        <v-col cols="12" class="text-center">
          <p class="text-caption text-medium-emphasis mb-0">
            &copy; {{ currentYear }} {{ appName }}. All rights reserved.
            <span class="mx-2">|</span>
            <router-link to="/privacy" class="text-decoration-none text-primary">
              Privacy Policy
            </router-link>
            <span class="mx-2">|</span>
            <router-link to="/terms" class="text-decoration-none text-primary">
              Terms of Service
            </router-link>
          </p>
        </v-col>
      </v-row>
    </v-container>
  </v-footer>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const appName = import.meta.env.VITE_APP_NAME || 'A.V.A.R'
const appTitle = import.meta.env.VITE_APP_TITLE || 'Authentic Visual Art Recognition Platform'

const currentYear = computed(() => new Date().getFullYear())

const quickLinks = [
  { title: 'Home', path: '/' },
  { title: 'Competitions', path: '/competitions' },
  { title: 'About', path: '/about' },
  { title: 'Contact', path: '/contact' },
]

const resourceLinks = [
  { title: 'API Documentation', href: '/docs/api' },
  { title: 'Help Center', href: '/help' },
  { title: 'FAQs', href: '/faq' },
  { title: 'Guidelines', href: '/guidelines' },
]

const socialLinks = [
  { name: 'GitHub', icon: 'mdi-github', href: 'https://github.com' },
  { name: 'Twitter', icon: 'mdi-twitter', href: 'https://twitter.com' },
  { name: 'Facebook', icon: 'mdi-facebook', href: 'https://facebook.com' },
  { name: 'Instagram', icon: 'mdi-instagram', href: 'https://instagram.com' },
]
</script>

<style scoped>
.border-t {
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}
</style>
