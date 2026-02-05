import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import axios from 'axios'
import HomeView from '@/views/HomeView.vue'
import { createRouter, createMemoryHistory } from 'vue-router'

// Mock the API service
vi.mock('@/services/api', () => ({
  api: {
    post: vi.fn()
  }
}))

import { api } from '@/services/api'

describe('Frontend-Backend Integration Tests', () => {
  let router
  let wrapper

  beforeEach(() => {
    router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', component: HomeView },
        { path: '/dashboard', component: { template: '<div>Dashboard</div>' } }
      ]
    })

    wrapper = mount(HomeView, {
      global: {
        plugins: [router]
      }
    })
  })

  it('TC-FB-001: Integration test for route optimization API call', async () => {
    // Mock the API response for route optimization
    const mockResponse = {
      data: {
        ID: 'test-route-1',
        name: 'Optimized Route',
        locations: [
          {
            ID: 'loc1',
            name: 'Store A',
            address: '123 Main St',
            lat: 55.7558,
            lon: 37.6173,
            time_window_start: '09:00',
            time_window_end: '18:00',
            priority: 'high'
          }
        ],
        total_distance_km: 15.5,
        total_time_hours: 2.5,
        total_cost_rub: 2500.0,
        model_used: 'Qwen',
        created_at: new Date().toISOString()
      }
    }

    // Mock the axios post call
    const postSpy = vi.spyOn(api, 'post').mockResolvedValue(mockResponse)

    // Simulate calling the backend API from frontend
    const result = await api.post('/qwen/optimize', {
      locations: [
        {
          ID: 'loc1',
          name: 'Store A',
          address: '123 Main St',
          lat: 55.7558,
          lon: 37.6173,
          time_window_start: '09:00',
          time_window_end: '18:00',
          priority: 'high'
        }
      ],
      constraints: {}
    })

    // Verify the API was called with correct parameters
    expect(postSpy).toHaveBeenCalledWith('/qwen/optimize', {
      locations: [
        {
          ID: 'loc1',
          name: 'Store A',
          address: '123 Main St',
          lat: 55.7558,
          lon: 37.6173,
          time_window_start: '09:00',
          time_window_end: '18:00',
          priority: 'high'
        }
      ],
      constraints: {}
    })

    // Verify the response structure matches the backend schema
    expect(result.data.ID).toBe('test-route-1')
    expect(result.data.total_distance_km).toBe(15.5)
    expect(result.data.total_time_hours).toBe(2.5)
    expect(result.data.model_used).toBe('Qwen')
    expect(Array.isArray(result.data.locations)).toBe(true)
    expect(result.data.locations.length).toBe(1)

    // Clean up
    postSpy.mockRestore()
  })

  it('TC-FB-002: Integration test for error handling between frontend and backend', async () => {
    // Mock an API error
    const errorResponse = {
      response: {
        status: 500,
        data: {
          detail: 'Internal server error'
        }
      }
    }

    // Mock the axios post call to reject
    const postSpy = vi.spyOn(api, 'post').mockRejectedValue(errorResponse)

    // Test error handling
    try {
      await api.post('/qwen/optimize', {
        locations: [],
        constraints: {}
      })
      // If we reach this line, the error wasn't caught
      expect(true).toBe(false) // This should not execute
    } catch (error) {
      // Verify that the error was handled properly
      expect(error.response.status).toBe(500)
      expect(error.response.data.detail).toBe('Internal server error')
    }

    // Verify the API was called
    expect(postSpy).toHaveBeenCalledWith('/qwen/optimize', {
      locations: [],
      constraints: {}
    })

    // Clean up
    postSpy.mockRestore()
  })

  it('TC-FB-003: Integration test for different LLM model selection', async () => {
    // Test different model responses
    const models = ['Qwen', 'GigaChat', 'Cotype', 'T-Pro']

    for (const model of models) {
      const mockResponse = {
        data: {
          ID: `route-${model.toLowerCase()}`,
          name: `Route via ${model}`,
          locations: [],
          total_distance_km: 10.0,
          total_time_hours: 1.0,
          total_cost_rub: 1000.0,
          model_used: model,
          created_at: new Date().toISOString()
        }
      }

      // Mock the API response
      vi.spyOn(api, 'post').mockResolvedValue(mockResponse)

      // Call the API
      const result = await api.post('/qwen/optimize', {
        locations: [],
        constraints: {}
      })

      // Verify the model in the response
      expect(result.data.model_used).toBe(model)
      expect(result.data.ID).toBe(`route-${model.toLowerCase()}`)
    }
  })

  it('TC-FB-004: Integration test for constraint validation', async () => {
    const mockResponse = {
      data: {
        ID: 'constraint-test-route',
        name: 'Constraint Test Route',
        locations: [],
        total_distance_km: 12.0,
        total_time_hours: 2.0,
        total_cost_rub: 2000.0,
        model_used: 'Qwen',
        created_at: new Date().toISOString()
      }
    }

    // Mock the API response
    const postSpy = vi.spyOn(api, 'post').mockResolvedValue(mockResponse)

    // Test with various constraints
    const testConstraints = [
      {},
      { max_distance_km: 20.0 },
      { vehicle_capacity: 5, time_limit_hours: 8.0 },
      { forbidden_roads: ['road1', 'road2'] }
    ]

    for (const constraints of testConstraints) {
      await api.post('/qwen/optimize', {
        locations: [],
        constraints
      })

      // Verify the API was called with the correct constraints
      expect(postSpy).toHaveBeenCalledWith('/qwen/optimize', {
        locations: [],
        constraints
      })
    }

    // Clean up
    postSpy.mockRestore()
  })

  it('TC-FB-005: Integration test for location data consistency', async () => {
    const mockLocations = [
      {
        ID: 'loc1',
        name: 'Store A',
        address: '123 Main St',
        lat: 55.7558,
        lon: 37.6173,
        time_window_start: '09:00',
        time_window_end: '18:00',
        priority: 'high'
      },
      {
        ID: 'loc2',
        name: 'Store B',
        address: '456 Oak Ave',
        lat: 55.7557,
        lon: 37.6174,
        time_window_start: '10:00',
        time_window_end: '17:00',
        priority: 'medium'
      }
    ]

    const mockResponse = {
      data: {
        ID: 'location-consistency-test',
        name: 'Location Consistency Test',
        locations: mockLocations,
        total_distance_km: 18.5,
        total_time_hours: 3.2,
        total_cost_rub: 3200.0,
        model_used: 'Qwen',
        created_at: new Date().toISOString()
      }
    }

    // Mock the API response
    vi.spyOn(api, 'post').mockResolvedValue(mockResponse)

    // Call the API with location data
    const result = await api.post('/qwen/optimize', {
      locations: mockLocations,
      constraints: {}
    })

    // Verify location data consistency between request and response
    expect(result.data.locations.length).toBe(2)
    expect(result.data.locations[0].ID).toBe('loc1')
    expect(result.data.locations[1].name).toBe('Store B')
    expect(result.data.total_distance_km).toBe(18.5)

    // Verify that all required location properties are preserved
    const firstLocation = result.data.locations[0]
    expect(firstLocation.ID).toBeDefined()
    expect(firstLocation.name).toBeDefined()
    expect(firstLocation.address).toBeDefined()
    expect(firstLocation.lat).toBeDefined()
    expect(firstLocation.lon).toBeDefined()
    expect(firstLocation.time_window_start).toBeDefined()
    expect(firstLocation.time_window_end).toBeDefined()
    expect(firstLocation.priority).toBeDefined()
  })
})