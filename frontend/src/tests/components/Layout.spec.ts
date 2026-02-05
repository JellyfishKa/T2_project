// tests/components/Layout.spec.ts - упрощенная версия
import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../../components/Layout.vue'

describe('Layout.vue', () => {
  const router = createRouter({
    history: createWebHistory(),
    routes: [{ path: '/', component: { template: '<div>Test</div>' } }]
  })

  beforeEach(async () => {
    await router.push('/')
  })

  it('рендерит основной layout', () => {
    const wrapper = mount(Layout, {
      global: {
        plugins: [router]
      }
    })
    
    // Проверяем основные элементы
    expect(wrapper.find('.min-h-screen').exists()).toBe(true)
    expect(wrapper.find('header').exists()).toBe(true)
    expect(wrapper.find('main').exists()).toBe(true)
  })

  it('имеет кнопку toggle sidebar', () => {
    const wrapper = mount(Layout, {
      global: {
        plugins: [router]
      }
    })
    
    // Проверяем, что кнопка есть (она в Header компоненте)
    // Поскольку Header зарендерен, ищем кнопку внутри него
    expect(wrapper.find('button.lg\\:hidden').exists()).toBe(true)
  })

  it('отображает контент через router-view', () => {
    const wrapper = mount(Layout, {
      global: {
        plugins: [router]
      }
    })
    
    // Проверяем, что основной контент рендерится
    expect(wrapper.find('.mx-auto.max-w-7xl').exists()).toBe(true)
  })
})