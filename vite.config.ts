import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import { defineConfig } from 'vite'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  base: process.env.NODE_ENV === 'production' ? '/tailadmin-vuejs/' : '/',
  plugins: [vue(), vueJsx(), vueDevTools()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    proxy: {
      // Proxy DNSE REST API calls through Vite to avoid browser CORS in dev.
      // e.g. /dnse-proxy/dnse-market-data-service/api/stocks/FPT
      //   → https://services.entrade.com.vn/dnse-market-data-service/api/stocks/FPT
      '/dnse-proxy': {
        target: 'https://services.entrade.com.vn',
        changeOrigin: true,
        secure: true,
        rewrite: (path) => path.replace(/^\/dnse-proxy/, ''),
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: undefined,
      },
    },
  },
})
