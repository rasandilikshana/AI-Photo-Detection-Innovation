<template>
  <v-container class="fill-height">
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="6" class="text-center">
        <v-icon size="120" color="warning" class="mb-6">mdi-lock-alert</v-icon>
        <h1 class="text-h2 font-weight-bold mb-4">403</h1>
        <h2 class="text-h4 mb-4">Access Forbidden</h2>
        <p class="text-body-1 text-medium-emphasis mb-8">
          You don't have permission to access this page. This area is restricted to certain user roles.
        </p>
        <div class="d-flex justify-center gap-4">
          <v-btn
            color="primary"
            size="large"
            @click="goBack"
          >
            <v-icon start>mdi-arrow-left</v-icon>
            Go Back
          </v-btn>
          <v-btn
            :to="{ name: 'home' }"
            variant="outlined"
            color="primary"
            size="large"
          >
            <v-icon start>mdi-home</v-icon>
            Home
          </v-btn>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

function goBack() {
  router.back()
}
</script>

<style scoped>
.gap-4 {
  gap: 1rem;
}
</style>
