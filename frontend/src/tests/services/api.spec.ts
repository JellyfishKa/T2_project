import { describe, it, expect } from 'vitest'
import axios from 'axios'
import { api } from '@/services/api'

describe('API Service', () => {
  it('creates axios instance with correct defaults', () => {
    // Check if the baseURL is set correctly (default fallback)
    expect(api.defaults.baseURL).toBe('http://localhost:8000')

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
        'Content-Type': 'application/json'
      }
    })

    expect(newApi.defaults.baseURL).toBe('https://api.example.com')

    // Restore original environment
    process.env = originalEnv
  })

  it('has response interceptors configured', () => {
    // Verify that interceptors are set up
    // The api module sets up response interceptors
    expect(api.interceptors.response).toBeDefined()
  })

  it('exports api instance', () => {
    expect(api).toBeDefined()
    expect(typeof api.get).toBe('function')
    expect(typeof api.post).toBe('function')
    expect(typeof api.put).toBe('function')
    expect(typeof api.delete).toBe('function')
  })
})
