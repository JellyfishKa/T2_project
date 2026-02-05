import { mount } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import Layout from '@/components/Layout.vue'
import Header from '@/components/Header.vue'
import Sidebar from '@/components/Sidebar.vue'
import { createRouter, createMemoryHistory } from 'vue-router'

// Create a minimal router for testing
const history = createMemoryHistory()
const router = createRouter({
  history,
  routes: [
    { path: '/', component: { template: '<div>Home</div>' } }
  ]
})

describe('Layout.vue', () => {
  it('renders header and main content', () => {
    const wrapper = mount(Layout, {
      global: {
        plugins: [router]
      }
    })

    // Check if the Header component is rendered
    expect(wrapper.findComponent(Header).exists()).toBe(true)
    
    // Check if the main content area exists
    expect(wrapper.find('main').exists()).toBe(true)
    
    // Check if the router view exists
    expect(wrapper.find('router-view-stub').exists()).toBe(true)
  })

  it('manages sidebar state correctly', async () => {
    const wrapper = mount(Layout, {
      global: {
        plugins: [router]
      }
    })

    // Initially sidebar should be closed
    expect(wrapper.vm.isSidebarOpen).toBe(false)

    // Trigger the toggle-sidebar event from the header
    const header = wrapper.findComponent(Header)
    await header.vm.$emit('toggle-sidebar')

    // Sidebar should now be open
    expect(wrapper.vm.isSidebarOpen).toBe(true)

    // Close the sidebar
    await wrapper.findComponent(Sidebar).vm.$emit('close')
    expect(wrapper.vm.isSidebarOpen).toBe(false)
  })

  it('handles escape key to close sidebar', async () => {
    const wrapper = mount(Layout, {
      global: {
        plugins: [router]
      }
    })

    // Open the sidebar
    await wrapper.setData({ isSidebarOpen: true })
    expect(wrapper.vm.isSidebarOpen).toBe(true)

    // Simulate pressing the escape key
    const event = new KeyboardEvent('keydown', { key: 'Escape' })
    window.dispatchEvent(event)

    // Sidebar should be closed after escape key press
    expect(wrapper.vm.isSidebarOpen).toBe(false)
  })

  it('closes sidebar when clicking overlay on mobile', async () => {
    const wrapper = mount(Layout, {
      global: {
        plugins: [router]
      }
    })

    // Open the sidebar
    await wrapper.setData({ isSidebarOpen: true })
    expect(wrapper.vm.isSidebarOpen).toBe(true)

    // Click on the overlay div
    const overlayDiv = wrapper.find('.fixed.inset-0.z-40.lg\\\\:hidden')
    if (overlayDiv.exists()) {
      await overlayDiv.trigger('click')
      // Wait for reactivity to update
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.isSidebarOpen).toBe(false)
    }
  })
})