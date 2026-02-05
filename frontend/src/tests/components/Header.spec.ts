import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import Header from '../../components/Header.vue'

describe('Header.vue', () => {
  const router = createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', component: { template: '<div>Home</div>' } },
      { path: '/dashboard', component: { template: '<div>Dashboard</div>' } },
      { path: '/optimize', component: { template: '<div>Optimize</div>' } },
      { path: '/analytics', component: { template: '<div>Analytics</div>' } },
    ]
  })

  it('рендерит логотип и название платформы', () => {
    const wrapper = mount(Header, {
      global: {
        plugins: [router]
      }
    })
    
    expect(wrapper.find('h1').text()).toBe('LLM Platform')
    expect(wrapper.find('p.text-gray-500').text()).toBe('AI Models Dashboard')
  })

  it('содержит кнопку toggle sidebar для мобильных устройств', () => {
    const wrapper = mount(Header, {
      global: {
        plugins: [router]
      }
    })
    
    const toggleButton = wrapper.find('button.lg\\:hidden')
    expect(toggleButton.exists()).toBe(true)
    expect(toggleButton.attributes('aria-label')).toBe('Open sidebar')
  })

  it('эмитит событие при клике на кнопку toggle sidebar', async () => {
    const wrapper = mount(Header, {
      global: {
        plugins: [router]
      }
    })
    
    const toggleButton = wrapper.find('button.lg\\:hidden')
    await toggleButton.trigger('click')
    
    expect(wrapper.emitted()).toHaveProperty('toggle-sidebar')
  })

  it('отображает навигационные ссылки', async () => {
    await router.push('/')
    const wrapper = mount(Header, {
      global: {
        plugins: [router]
      }
    })
    
    const navItems = ['Home', 'Dashboard', 'Optimize', 'Analytics']
    navItems.forEach(item => {
      expect(wrapper.text()).toContain(item)
    })
  })

  it('показывает активную навигационную ссылку', async () => {
    await router.push('/dashboard')
    const wrapper = mount(Header, {
      global: {
        plugins: [router]
      }
    })
    
    const activeLink = wrapper.find('.text-blue-600.bg-blue-50')
    expect(activeLink.exists()).toBe(true)
    expect(activeLink.text()).toBe('Dashboard')
  })

  it('скрывает описание на мобильных устройствах', () => {
    const wrapper = mount(Header, {
      global: {
        plugins: [router]
      }
    })
    
    const description = wrapper.find('p.text-gray-500')
    expect(description.classes()).toContain('hidden')
    expect(description.classes()).toContain('sm:block')
  })

  it('содержит логотип с правильными стилями', () => {
    const wrapper = mount(Header, {
      global: {
        plugins: [router]
      }
    })
    
    const logo = wrapper.find('.bg-black.rounded-lg')
    expect(logo.exists()).toBe(true)
    expect(logo.classes()).toContain('h-8')
    expect(logo.classes()).toContain('w-8')
    expect(logo.find('span').text()).toBe('T2')
  })
})