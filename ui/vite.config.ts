import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/n8n-webhook': {
        target: 'http://localhost:5678',
        rewrite: (path) => path.replace(/^\/n8n-webhook/, '/webhook'),
        changeOrigin: true,
      },
    },
  },
})
