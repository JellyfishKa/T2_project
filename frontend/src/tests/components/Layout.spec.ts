import { mount, shallowMount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import Layout from '@/components/Layout.vue'
import Header from '@/components/Header.vue'
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

describe('Layout.vue', () => {
  it('renders header and main content', () => {
    const wrapper = shallowMount(Layout, {
      global: {
        plugins: [router],
        stubs: {
          Header: true,
          Sidebar: true,
          RouterView: true,
          Transition: true
        }
      }
    })

    // Check if the Header component is rendered
    expect(wrapper.findComponent({ name: 'Header' }).exists() || wrapper.find('header-stub').exists()).toBe(true)

    // Check if the main content area exists
    expect(wrapper.find('main').exists()).toBe(true)

    // Check if the router view exists (as stub)
    expect(wrapper.find('router-view-stub').exists()).toBe(true)
  })

  it('shows/hides sidebar when toggle event is triggered', async () => {
    const wrapper = mount(Layout, {
      global: {
        plugins: [router],
        stubs: {
          Transition: false
        }
      }
    })

    // Initially sidebar should not show the mobile version (isSidebarOpen is false)
    expect(wrapper.find('.fixed.inset-0.z-40').exists()).toBe(false)

    // Trigger the toggle-sidebar event from the header
    const header = wrapper.findComponent(Header)
    await header.vm.$emit('toggle-sidebar')
    await wrapper.vm.$nextTick()

    // Mobile overlay should now be visible
    expect(wrapper.find('.fixed.inset-0.z-40').exists()).toBe(true)
  })

  it('closes sidebar when clicking overlay on mobile', async () => {
    const wrapper = mount(Layout, {
      global: {
        plugins: [router],
        stubs: {
          Transition: false
        }
      }
    })

    // Open the sidebar first via header toggle
    const header = wrapper.findComponent(Header)
    await header.vm.$emit('toggle-sidebar')
    await wrapper.vm.$nextTick()

    // Check overlay is visible
    expect(wrapper.find('.fixed.inset-0.z-40').exists()).toBe(true)

    // Click on the overlay div
    const overlayDiv = wrapper.find('.fixed.inset-0.z-40')
    await overlayDiv.trigger('click')
    await wrapper.vm.$nextTick()

    // Overlay should be hidden now
    expect(wrapper.find('.fixed.inset-0.z-40').exists()).toBe(false)
  })
})
