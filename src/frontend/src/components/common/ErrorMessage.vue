<template>
  <v-alert
    v-if="message"
    :type="type"
    :variant="variant"
    :closable="closable"
    :icon="icon"
    class="mb-4"
    @click:close="emit('close')"
  >
    <template v-if="title" #title>
      {{ title }}
    </template>
    {{ message }}
  </v-alert>
</template>

<script setup lang="ts">
interface Props {
  message?: string
  title?: string
  type?: 'error' | 'warning' | 'info' | 'success'
  variant?: 'tonal' | 'outlined' | 'flat' | 'text'
  closable?: boolean
  icon?: string | boolean
}

withDefaults(defineProps<Props>(), {
  message: '',
  title: '',
  type: 'error',
  variant: 'tonal',
  closable: true,
  icon: true,
})

const emit = defineEmits<{
  close: []
}>()
</script>
