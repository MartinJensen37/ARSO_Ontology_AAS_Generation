import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Proxy targets are overridable via env so the same config works both for
// native dev (backend reachable at localhost) and inside Docker Compose
// (backend reachable at its service name -- see docker-compose.yml).
const apiTarget = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000';
const n8nTarget = process.env.VITE_N8N_PROXY_TARGET || 'http://localhost:5678';

export default defineConfig({
  plugins: [react()],
  server: {
    // Bind 0.0.0.0, not just localhost -- required for the dev server to be
    // reachable from outside its container via the docker-compose port mapping.
    host: true,
    proxy: {
      '/api': apiTarget,
      '/n8n-webhook': {
        target: n8nTarget,
        rewrite: (path) => path.replace(/^\/n8n-webhook/, '/webhook'),
        changeOrigin: true,
      },
    },
  },
})
