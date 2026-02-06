import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import Sidebar from '@/components/Sidebar.vue'
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

describe('Sidebar.vue', () => {
  it('renders sidebar with navigation items', () => {
    const wrapper = mount(Sidebar, {
      global: {
        plugins: [router]
      }
    })

    // Check if the sidebar header is rendered
    expect(wrapper.find('.h-16.items-center').exists()).toBe(true)
    
    // Check if navigation items exist
    const navLinks = wrapper.findAll('a')
    expect(navLinks.length).toBe(4) // Home, Dashboard, Optimize, Analytics
    
    // Check if the close button exists for mobile view
    expect(wrapper.find('button').exists()).toBe(true)
  })

  it('emits close event when close button is clicked', async () => {
    const wrapper = mount(Sidebar, {
      global: {
        plugins: [router]
      }
    })

    // Find and click the close button
    const closeButton = wrapper.find('button')
    await closeButton.trigger('click')

    // Check if the close event was emitted
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('emits close event when navigation item is clicked', async () => {
    const wrapper = mount(Sidebar, {
      global: {
        plugins: [router]
      }
    })

    // Navigate to dashboard first
    await router.push('/dashboard')
    await router.isReady()

    // Find the first navigation link (Home) and click it
    const navLinks = wrapper.findAll('a')
    if (navLinks.length > 0) {
      await navLinks[0].trigger('click')
      
      // Check if the close event was emitted
      expect(wrapper.emitted('close')).toBeTruthy()
    }
  })

  it('highlights active navigation item', async () => {
    // Navigate to dashboard
    await router.push('/dashboard')
    await router.isReady()

    const wrapper = mount(Sidebar, {
      global: {
        plugins: [router]
      }
    })

    // Check if the dashboard link is highlighted
    const dashboardLink = wrapper.findAll('a').find((link: any) => link.text().includes('Dashboard'))
    expect(dashboardLink?.classes()).toContain('text-blue-600')
    expect(dashboardLink?.classes()).toContain('bg-blue-50')
  })
})