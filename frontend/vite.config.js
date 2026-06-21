import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const isDev = mode === 'development'

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: isDev
        ? {
            // API REST
            '/api': {
              target: 'http://localhost:8000',
              changeOrigin: true,
              rewrite: (path) => path.replace(/^\/api/, '/_/backend/api'),
            },
            // WebSocket
            '/ws': {
              target: 'ws://localhost:8000',
              ws: true,
              changeOrigin: true,
              rewrite: (path) => path.replace(/^\/ws/, '/_/backend/ws'),
            },
          }
        : undefined,
    },
  }
})

