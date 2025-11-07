/**
 * Main Application Entry Point
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'
import './style.css'

// Import auth store to initialize authentication
import { useAuthStore } from './store/auth'

// Create Vue app
const app = createApp(App)

// Create Pinia instance
const pinia = createPinia()

// Register plugins
app.use(pinia) // Register Pinia first
app.use(router)
app.use(vuetify)
app.use(Toast, {
  position: 'top-right',
  timeout: 3000,
  closeOnClick: true,
  pauseOnFocusLoss: true,
  pauseOnHover: true,
  draggable: true,
  draggablePercent: 0.6,
  showCloseButtonOnHover: false,
  hideProgressBar: false,
  closeButton: 'button',
  icon: true,
  rtl: false,
})

// Mount app
app.mount('#app')

// Initialize auth state after mounting
const authStore = useAuthStore()
authStore.initializeAuth()
