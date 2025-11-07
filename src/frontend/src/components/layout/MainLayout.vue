<template>
  <v-app>
    <!-- App Header -->
    <AppHeader @toggle-drawer="drawer = !drawer" />

    <!-- App Sidebar -->
    <AppSidebar v-model="drawer" />

    <!-- Main Content -->
    <v-main>
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </v-main>

    <!-- App Footer -->
    <AppFooter />
  </v-app>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AppHeader from './AppHeader.vue'
import AppFooter from './AppFooter.vue'
import AppSidebar from './AppSidebar.vue'

const drawer = ref(false)
</script>

<style scoped>
/* Fade transition for route changes */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
