/**
 * Vuetify Plugin Configuration
 * Material Design 3 theme with custom A.V.A.R. colors
 */

import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { aliases, mdi } from 'vuetify/iconsets/mdi'
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

// Custom theme colors
const customTheme = {
  dark: false,
  colors: {
    primary: '#1976D2',      // Blue - Trust, professionalism
    secondary: '#424242',    // Dark Grey - Sophistication
    accent: '#FF6F00',       // Orange - Energy, creativity
    success: '#4CAF50',      // Green
    warning: '#FFC107',      // Amber
    error: '#F44336',        // Red
    info: '#2196F3',         // Light Blue
    background: '#FAFAFA',   // Light background
    surface: '#FFFFFF',      // White
    'on-surface': '#212121', // Text on surface
  },
}

export default createVuetify({
  components,
  directives,

  // Icon configuration
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: {
      mdi,
    },
  },

  // Theme configuration
  theme: {
    defaultTheme: 'customTheme',
    themes: {
      customTheme,
    },
  },

  // Default props for components
  defaults: {
    VBtn: {
      elevation: 2,
      rounded: 'md',
    },
    VCard: {
      elevation: 2,
      rounded: 'lg',
    },
    VTextField: {
      variant: 'outlined',
      density: 'comfortable',
    },
    VSelect: {
      variant: 'outlined',
      density: 'comfortable',
    },
  },
})
