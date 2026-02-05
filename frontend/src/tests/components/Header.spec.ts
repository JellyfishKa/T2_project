import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import Header from '@/components/Header.vue'
import { createRouter, createMemoryHistory } from 'vue-router'

// Create a minimal router for testing
const history = createMemoryHistory()
const router = createRouter({
  history,
  routes: [
    { path: '/', component: { template: '<div>Home</div>' } },
    { path: '/dashboard', component: { template: '<div>Dashboard</div>' } },
    { path: '/optimize', component: { template: '<div>Optimize</div>' } },
    { path: '/analytics', component: { template: '<div>Analytics</div>' } }
  ]
})

describe('Header.vue', () => {
  it('renders header with logo and title', () => {
    const wrapper = mount(Header, {
      global: {
        plugins: [router]
      }
    })

    // Check if the logo is rendered
    expect(wrapper.find('.h-8.w-8.bg-black').exists()).toBe(true)
    
    // Check if the title is rendered
    expect(wrapper.text()).toContain('LLM Platform')
    
    // Check if the navigation items exist
    expect(wrapper.findAll('a').length).toBeGreaterThan(0)
  })

  it('emits toggle-sidebar event when menu button is clicked', async () => {
    const wrapper = mount(Header, {
      global: {
        plugins: [router]
      }
    })

    // Find and click the mobile menu button
    const menuButton = wrapper.find('button')
    await menuButton.trigger('click')

    // Check if the event was emitted
    expect(wrapper.emitted('toggle-sidebar')).toBeTruthy()
  })

  it('highlights active navigation item', async () => {
    // Navigate to dashboard
    await router.push('/dashboard')
    await router.isReady()

    const wrapper = mount(Header, {
      global: {
        plugins: [router]
      }
    })

    // Check if the dashboard link is highlighted
    const dashboardLink = wrapper.findAll('a').find(link => link.text().includes('Dashboard'))
    expect(dashboardLink?.classes()).toContain('text-blue-600')
    expect(dashboardLink?.classes()).toContain('bg-blue-50')
  })
})