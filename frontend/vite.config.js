import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // In development the FastAPI backend runs separately on port 8001.
    // In production both are served from the same origin.
    proxy: {
      '/api': 'http://127.0.0.1:8001',
    },
  },
})
