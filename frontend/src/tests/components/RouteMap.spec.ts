import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import RouteMap from '@/components/RouteMap.vue'

describe('RouteMap.vue', () => {
  it('renders the route map component with title', () => {
    const wrapper = mount(RouteMap)

    // Check if the title is rendered
    expect(wrapper.find('h2').text()).toBe('Route Map')
    
    // Check if the placeholder content is displayed
    expect(wrapper.text()).toContain('Map visualization will be implemented here')
    
    // Check if the container has the correct classes
    expect(wrapper.classes()).toContain('border')
    expect(wrapper.classes()).toContain('rounded-lg')
    expect(wrapper.classes()).toContain('p-4')
    expect(wrapper.classes()).toContain('h-96')
  })

  it('has the correct structure', () => {
    const wrapper = mount(RouteMap)

    // Check if the main container div exists
    const container = wrapper.find('.border.rounded-lg.p-4.h-96')
    expect(container.exists()).toBe(true)
    
    // Check if the inner content div exists
    const contentDiv = wrapper.find('.bg-gray-100.h-full.flex.items-center.justify-center')
    expect(contentDiv.exists()).toBe(true)
  })
})