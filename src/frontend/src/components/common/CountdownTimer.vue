<template>
  <div class="countdown-timer">
    <div v-if="!isExpired" class="timer-display">
      <div v-if="showLabel" class="timer-label text-caption text-medium-emphasis mb-2">
        {{ label }}
      </div>
      <div class="timer-units d-flex justify-center gap-3">
        <div v-if="days > 0" class="time-unit">
          <div class="time-value text-h4 font-weight-bold">{{ padZero(days) }}</div>
          <div class="time-label text-caption">Days</div>
        </div>
        <div class="time-unit">
          <div class="time-value text-h4 font-weight-bold">{{ padZero(hours) }}</div>
          <div class="time-label text-caption">Hours</div>
        </div>
        <div class="time-unit">
          <div class="time-value text-h4 font-weight-bold">{{ padZero(minutes) }}</div>
          <div class="time-label text-caption">Minutes</div>
        </div>
        <div class="time-unit">
          <div class="time-value text-h4 font-weight-bold">{{ padZero(seconds) }}</div>
          <div class="time-label text-caption">Seconds</div>
        </div>
      </div>
    </div>
    <div v-else class="expired-message">
      <v-icon size="large" :color="expiredColor" class="mb-2">
        {{ expiredIcon }}
      </v-icon>
      <p class="text-h6 font-weight-medium" :class="`text-${expiredColor}`">
        {{ expiredMessage }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

interface Props {
  targetDate: string | Date
  label?: string
  showLabel?: boolean
  expiredMessage?: string
  expiredIcon?: string
  expiredColor?: string
}

const props = withDefaults(defineProps<Props>(), {
  label: 'Time Remaining',
  showLabel: true,
  expiredMessage: 'Time has expired',
  expiredIcon: 'mdi-clock-alert',
  expiredColor: 'error',
})

const emit = defineEmits<{
  expired: []
}>()

const now = ref(Date.now())
let interval: number | null = null

const targetTimestamp = computed(() => {
  return new Date(props.targetDate).getTime()
})

const timeRemaining = computed(() => {
  return Math.max(0, targetTimestamp.value - now.value)
})

const isExpired = computed(() => timeRemaining.value === 0)

const days = computed(() => Math.floor(timeRemaining.value / (1000 * 60 * 60 * 24)))
const hours = computed(() => Math.floor((timeRemaining.value % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)))
const minutes = computed(() => Math.floor((timeRemaining.value % (1000 * 60 * 60)) / (1000 * 60)))
const seconds = computed(() => Math.floor((timeRemaining.value % (1000 * 60)) / 1000))

function padZero(num: number): string {
  return num.toString().padStart(2, '0')
}

function updateTime() {
  const previousExpired = isExpired.value
  now.value = Date.now()

  if (!previousExpired && isExpired.value) {
    emit('expired')
  }
}

onMounted(() => {
  interval = window.setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (interval) {
    clearInterval(interval)
  }
})
</script>

<style scoped>
.countdown-timer {
  text-align: center;
}

.timer-units {
  gap: 1.5rem;
}

.time-unit {
  min-width: 60px;
}

.time-value {
  line-height: 1;
  margin-bottom: 0.25rem;
}

.time-label {
  text-transform: uppercase;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.expired-message {
  padding: 2rem;
}

.gap-3 {
  gap: 1rem;
}
</style>
