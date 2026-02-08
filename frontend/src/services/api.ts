import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Mock interceptor for development
api.interceptors.response.use(
  (config) => {
    if (import.meta.env.DEV) {
      // Return mock data in development
      console.log('Mock interceptor active')
    }
    return config
  },
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)
