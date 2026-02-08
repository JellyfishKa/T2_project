import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@':  path.resolve(__dirname, './src')
    }
  },
  server: {
    port: parseInt(process.env.FRONTEND_PORT || '5173'),
    host: true
  },
  build: {
    target: 'es2020',
    outDir: 'dist',
    sourcemap: true
  }
})