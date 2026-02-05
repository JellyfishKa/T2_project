import { config } from '@vue/test-utils'
import '@testing-library/jest-dom'

// Глобальные настройки для тестов
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}