import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Proxy targets are env-overridable: localhost natively, service name in Compose.
const apiTarget = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000';
const n8nTarget = process.env.VITE_N8N_PROXY_TARGET || 'http://localhost:5678';

export default defineConfig({
  plugins: [react()],
  server: {
    // Bind 0.0.0.0 so the dev server is reachable through the container port map.
    host: true,
    // Docker Desktop bind mounts don't forward filesystem events reliably, so
    // polling is on unconditionally.
    watch: {
      usePolling: true,
      interval: 300,
    },
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
