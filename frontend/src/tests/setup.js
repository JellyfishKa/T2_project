import { config } from '@vue/test-utils'

// Глобальные настройки для тестов
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
