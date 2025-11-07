<script setup lang="ts">
import { RouterView, useRoute } from 'vue-router'
import { computed } from 'vue'
import Layout from './components/Layout.vue'

const route = useRoute()

// Pages that don't need layout
const noLayoutPages = ['Login', 'Register']
const needsLayout = computed(() => !noLayoutPages.includes(route.name as string))
</script>

<template>
  <div id="app">
    <Layout v-if="needsLayout">
      <RouterView />
    </Layout>
    <RouterView v-else />
  </div>
</template>
