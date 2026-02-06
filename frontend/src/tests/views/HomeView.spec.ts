import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import HomeView from '@/views/HomeView.vue'
import { createRouter, createMemoryHistory } from 'vue-router'

// Create a minimal router for testing
const history = createMemoryHistory()
const router = createRouter({
  history,
  routes: [
    { path: '/', component: HomeView },
    { path: '/dashboard', component: { template: '<div>Dashboard</div>' } },
    { path: '/optimize', component: { template: '<div>Optimize</div>' } },
    { path: '/analytics', component: { template: '<div>Analytics</div>' } }
  ]
})

describe('HomeView.vue', () => {
  it('renders the home page with correct content', () => {
    const wrapper = mount(HomeView, {
      global: {
        plugins: [router]
      }
    })

    // Check if the main heading is rendered
    expect(wrapper.find('h1').text()).toBe('T2 Розничная сеть')

    // Check if the description is rendered
    expect(wrapper.text()).toContain(
      'Комплексная платформа на основе искусственного интеллекта'
    )

    // Check if the navigation section exists
    expect(wrapper.find('h2').text()).toBe('Навигация')
  })

  it('contains quick action links', () => {
    const wrapper = mount(HomeView, {
      global: {
        plugins: [router]
      }
    })

    // Check if all quick action links exist
    const links = wrapper.findAll('a')
    expect(links.length).toBe(4)

    // Check if the links have correct text
    const linkTexts = links.map((link) => link.text())
    expect(linkTexts).toContain('Dashboard')
    expect(linkTexts).toContain('Test Models')
    expect(linkTexts).toContain('Optimize')
    expect(linkTexts).toContain('Analytics')
  })

  it('links navigate to correct routes', () => {
    const wrapper = mount(HomeView, {
      global: {
        plugins: [router]
      }
    })

    // Check if links have correct to attributes
    const dashboardLink = wrapper.find('a[href="/dashboard"]')
    expect(dashboardLink.exists()).toBe(true)

    const optimizeLink = wrapper.find('a[href="/optimize"]')
    expect(optimizeLink.exists()).toBe(true)

    const analyticsLink = wrapper.find('a[href="/analytics"]')
    expect(analyticsLink.exists()).toBe(true)
  })
})
