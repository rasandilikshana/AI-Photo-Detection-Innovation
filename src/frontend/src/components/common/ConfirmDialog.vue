<template>
  <v-dialog :model-value="modelValue" max-width="500" @update:model-value="emit('update:modelValue', $event)">
    <v-card>
      <v-card-title class="text-h5 d-flex align-center">
        <v-icon :color="iconColor" class="mr-2">{{ icon }}</v-icon>
        {{ title }}
      </v-card-title>

      <v-card-text>
        {{ message }}
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          :text="cancelText"
          variant="text"
          @click="handleCancel"
        />
        <v-btn
          :text="confirmText"
          :color="confirmColor"
          variant="flat"
          :loading="loading"
          @click="handleConfirm"
        />
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
interface Props {
  modelValue: boolean
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  confirmColor?: string
  icon?: string
  iconColor?: string
  loading?: boolean
}

withDefaults(defineProps<Props>(), {
  title: 'Confirm Action',
  confirmText: 'Confirm',
  cancelText: 'Cancel',
  confirmColor: 'primary',
  icon: 'mdi-alert-circle',
  iconColor: 'warning',
  loading: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: []
  cancel: []
}>()

function handleConfirm() {
  emit('confirm')
}

function handleCancel() {
  emit('cancel')
  emit('update:modelValue', false)
}
</script>
