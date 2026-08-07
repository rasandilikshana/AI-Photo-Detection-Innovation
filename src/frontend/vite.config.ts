import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    // Dev-only: serve uploaded files through the competition service,
    // mirroring the nginx /uploads alias used in production.
    proxy: {
      '/uploads': 'http://localhost:8080',
    },
  },
})
