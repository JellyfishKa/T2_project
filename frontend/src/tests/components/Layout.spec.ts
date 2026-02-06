import { mount } from '@vue/test-utils'
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

  it('shows/hides sidebar when toggle event is triggered', async () => {
    const wrapper = mount(Layout, {
      global: {
        plugins: [router]
      }
    })

    // Initially sidebar should not be visible in mobile view
    expect(wrapper.find('.fixed.inset-y-0.left-0.z-50.w-64.lg\\\\:hidden').exists()).toBe(false)

    // Trigger the toggle-sidebar event from the header
    const header = wrapper.findComponent(Header)
    await header.vm.$emit('toggle-sidebar')

    // Sidebar should now be visible in mobile view
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.fixed.inset-y-0.left-0.z-50.w-64.lg\\\\:hidden').exists()).toBe(true)

    // Close the sidebar by emitting close event from sidebar
    const sidebar = wrapper.findComponent(Sidebar)
    await sidebar.vm.$emit('close')
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.fixed.inset-y-0.left-0.z-50.w-64.lg\\\\:hidden').exists()).toBe(false)
  })

  it('closes sidebar when clicking overlay on mobile', async () => {
    const wrapper = mount(Layout, {
      global: {
        plugins: [router]
      }
    })

    // Show the sidebar first
    await wrapper.setData({ isSidebarOpen: true })
    await wrapper.vm.$nextTick()
    
    // Check if sidebar is visible
    expect(wrapper.find('.fixed.inset-y-0.left-0.z-50.w-64.lg\\\\:hidden').exists()).toBe(true)

    // Click on the overlay div
    const overlayDiv = wrapper.find('.fixed.inset-0.z-40.lg\\\\:hidden')
    if (overlayDiv.exists()) {
      await overlayDiv.trigger('click')
      // Wait for reactivity to update
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.fixed.inset-y-0.left-0.z-50.w-64.lg\\\\:hidden').exists()).toBe(false)
    }
  })
})