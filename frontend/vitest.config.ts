import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true,
<<<<<<< Updated upstream
    environment: 'happy-dom',
    include: ['src/**/*.spec.ts'],
  }
=======
    setupFiles: ['./src/tests/setup.js'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules', 'src/tests', 'src/router/index.ts', 'src/main.ts', 'src/services/api.ts']
    }
  },
>>>>>>> Stashed changes
})