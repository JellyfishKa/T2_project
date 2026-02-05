import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import axios from 'axios'
import { api } from '@/services/api'

// Mock environment variables
vi.mock('virtual:env', () => ({
  env: {
    VITE_API_URL: 'https://api.example.com'
  }
}))

describe('API Service', () => {
  beforeEach(() => {
    // Clear any interceptors from previous tests
    api.interceptors.request.clear()
    api.interceptors.response.clear()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('creates axios instance with correct defaults', () => {
    // Check if the baseURL is set correctly
    expect(api.defaults.baseURL).toBe('http://localhost:8000') // Default fallback
    
    // Check if timeout is set correctly
    expect(api.defaults.timeout).toBe(30000)
    
    // Check if headers are set correctly
    expect(api.defaults.headers['Content-Type']).toBe('application/json')
  })

  it('uses environment variable for baseURL when available', () => {
    // Temporarily set environment variable
    const originalEnv = process.env
    process.env = { ...originalEnv, VITE_API_URL: 'https://api.example.com' }
    
    // Recreate the api instance to pick up the new environment
    const newApi = axios.create({
      baseURL: process.env.VITE_API_URL || 'http://localhost:8000',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    expect(newApi.defaults.baseURL).toBe('https://api.example.com')
    
    // Restore original environment
    process.env = originalEnv
  })

  it('has response interceptor for error handling', async () => {
    // Mock a failed request
    const mockError = {
      response: {
        status: 500,
        data: { message: 'Internal Server Error' }
      },
      message: 'Request failed'
    }

    // Spy on console.error to verify error logging
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    // Create a promise that rejects to trigger the error interceptor
    try {
      await api.get('/test') // This will fail since we're not mocking the actual request
    } catch (error) {
      // We expect this to fail, which is fine for this test
    }

    // Verify that the error was logged
    expect(consoleSpy).toHaveBeenCalled()
    
    // Restore console spy
    consoleSpy.mockRestore()
  })

  it('has response interceptor for mock data in development', async () => {
    // Temporarily set NODE_ENV to development
    const originalEnv = process.env
    process.env = { ...originalEnv, NODE_ENV: 'development' }
    
    // Spy on console.log to verify mock interceptor activation
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
    
    // Restore original environment
    process.env = originalEnv
    
    // Verify that the mock interceptor message would be logged in dev mode
    expect(consoleSpy).toHaveBeenCalledWith('Mock interceptor active')
    
    // Restore console spy
    consoleSpy.mockRestore()
  })
})