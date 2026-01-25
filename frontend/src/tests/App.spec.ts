import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import App from '../App.vue'

describe('тест', () => {
  it('рендерит название приложения', () => {
    const wrapper = mount(App, {
      global: {
        stubs: ['RouterLink', 'RouterView']
      }
    })
    
    // Проверяем что компонент отрисовывается
    expect(wrapper.html()).toBeDefined()
    
    // Проверяем наличие текста (хотя бы частично)
    const html = wrapper.html()
    expect(html).toContain('t2')

  })

  it('имеет правильную структуру DOM', () => {
    const wrapper = mount(App, {
      global: {
        stubs: ['RouterLink', 'RouterView']
      }
    })
    
    // Проверяем основные элементы
    expect(wrapper.find('header').exists()).toBe(true)
    expect(wrapper.find('nav').exists()).toBe(true)
    expect(wrapper.find('main').exists()).toBe(true)
    

  })
})