import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'

// Мокаем axios ДО импорта api
vi.mock('axios', () => {
  const mockAxiosInstance = {
    defaults: {
      timeout: 30000,
      baseURL: 'http://localhost:8000/api/v1',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json'
      }
    },
    interceptors: {
      request: { use: vi.fn(), eject: vi.fn() },
      response: { use: vi.fn(), eject: vi.fn() }
    },
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }

  const mockAxiosCreate = vi.fn().mockReturnValue(mockAxiosInstance)

  return {
    default: {
      ...mockAxiosInstance,
      create: mockAxiosCreate
    },
    create: mockAxiosCreate
  }
})

// Теперь импортируем api
import {
  uploadLocations,
  optimize,
  getMetrics,
  getInsights,
  compareModels,
  fetchRoutes,
  fetchRouteDetails,
  fetchRouteMetrics,
  runBenchmark,
  checkHealth,
  fetchAllLocations
} from '@/services/api'

describe('API Service', () => {
  const mockedAxios = vi.mocked(axios, true)

  beforeEach(() => {
    vi.resetAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('uploadLocations', () => {
    it('should successfully upload locations file', async () => {
      const mockResponse = {
        data: {
          success: true,
          message: 'Uploaded 5 locations',
          locations: [
            {
              id: 'loc-1',
              name: 'Store 1',
              latitude: 55.7558,
              longitude: 37.6173,
              address: 'Address 1',
              time_window_start: '09:00',
              time_window_end: '18:00',
              priority: 1
            }
          ]
        }
      }

      mockedAxios.post.mockResolvedValue(mockResponse)

      const file = new File(['test'], 'test.csv', { type: 'text/csv' })
      const result = await uploadLocations(file)

      expect(result.success).toBe(true)
      expect(result.locations).toHaveLength(1)
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/locations/upload',
        expect.any(FormData),
        expect.objectContaining({
          headers: { 'Content-Type': 'multipart/form-data' }
        })
      )
    })
  })

  describe('optimize', () => {
    it('should successfully optimize route', async () => {
      const mockRoute = {
        id: 'route-123',
        name: 'Optimized Route',
        locations: ['loc-1', 'loc-2'],
        total_distance_km: 25.5,
        total_time_hours: 2.5,
        total_cost_rub: 1500,
        model_used: 'qwen',
        fallback_reason: null,
        created_at: '2026-02-13T10:30:00Z'
      }

      mockedAxios.post.mockResolvedValue({ data: mockRoute })

      const result = await optimize(['loc-1', 'loc-2'], 'qwen', {
        max_distance_km: 100
      })

      expect(result.id).toBe('route-123')
      expect(result.model_used).toBe('qwen')
      expect(mockedAxios.post).toHaveBeenCalledWith('/optimize', {
        location_ids: ['loc-1', 'loc-2'],
        model: 'qwen',
        constraints: { max_distance_km: 100 }
      })
    })
  })

  describe('getMetrics', () => {
    it('should fetch all metrics', async () => {
      const mockMetrics = {
        metrics: [
          {
            id: 'metric-1',
            route_id: 'route-1',
            model: 'llama',
            response_time_ms: 1245,
            quality_score: 0.87,
            cost_rub: 25.5,
            timestamp: '2026-02-13T09:15:30Z'
          },
          {
            id: 'metric-2',
            route_id: 'route-2',
            model: 'qwen',
            response_time_ms: 432,
            quality_score: 0.82,
            cost_rub: 0,
            timestamp: '2026-02-13T09:16:15Z'
          }
        ]
      }

      mockedAxios.get.mockResolvedValue({ data: mockMetrics })

      const result = await getMetrics()

      expect(result.metrics).toHaveLength(2)
      expect(mockedAxios.get).toHaveBeenCalledWith('/metrics')
    })
  })

  describe('getInsights', () => {
    it('should fetch insights', async () => {
      const mockInsights = {
        total_routes: 42,
        total_distance_km: 1250.5,
        total_cost_rub: 87500,
        average_quality_score: 0.87,
        popular_models: [
          { model: 'qwen', count: 25 },
          { model: 'llama', count: 12 }
        ],
        cost_savings: {
          estimated_savings_rub: 12500,
          percentage: 12.5
        },
        recent_activity: [
          { date: '2026-02-10', routes_count: 5 },
          { date: '2026-02-11', routes_count: 8 },
          { date: '2026-02-12', routes_count: 12 },
          { date: '2026-02-13', routes_count: 7 }
        ]
      }

      mockedAxios.get.mockResolvedValue({ data: mockInsights })

      const result = await getInsights()

      expect(result.total_routes).toBe(42)
      expect(result.popular_models).toHaveLength(2)
      expect(mockedAxios.get).toHaveBeenCalledWith('/insights')
    })
  })

  describe('compareModels', () => {
    it('should fetch model comparison', async () => {
      const mockComparison = {
        models: [
          {
            name: 'qwen',
            avg_response_time_ms: 450,
            avg_quality_score: 0.82,
            total_cost_rub: 0,
            success_rate: 0.99,
            usage_count: 1250
          },
          {
            name: 'llama',
            avg_response_time_ms: 1250,
            avg_quality_score: 0.87,
            total_cost_rub: 2500,
            success_rate: 0.95,
            usage_count: 850
          }
        ],
        recommendations: [
          {
            scenario: 'Быстрые запросы, бюджет 0₽',
            recommended_model: 'qwen',
            reason: 'Бесплатно и очень быстро'
          },
          {
            scenario: 'Максимальная точность',
            recommended_model: 'llama',
            reason: 'Лучшее качество ответов'
          }
        ]
      }

      mockedAxios.get.mockResolvedValue({ data: mockComparison })

      const result = await compareModels()

      expect(result.models).toHaveLength(2)
      expect(result.recommendations).toHaveLength(2)
      expect(mockedAxios.get).toHaveBeenCalledWith('/benchmark/compare')
    })
  })

  describe('fetchRoutes', () => {
    it('should fetch paginated routes', async () => {
      const mockResponse = {
        data: {
          total: 10,
          items: [
            {
              id: 'route-1',
              name: 'Route 1',
              locations: ['loc-1'],
              total_distance_km: 10.5,
              total_time_hours: 1.5,
              total_cost_rub: 1250,
              model_used: 'llama',
              fallback_reason: null,
              created_at: '2026-02-13T09:15:00Z'
            },
            {
              id: 'route-2',
              name: 'Route 2',
              locations: ['loc-2'],
              total_distance_km: 25.3,
              total_time_hours: 3.2,
              total_cost_rub: 2500,
              model_used: 'qwen',
              fallback_reason: null,
              created_at: '2026-02-12T14:30:00Z'
            }
          ]
        }
      }

      mockedAxios.get.mockResolvedValue(mockResponse)

      const result = await fetchRoutes(0, 5)

      expect(result.total).toBe(10)
      expect(result.items).toHaveLength(2)
      expect(mockedAxios.get).toHaveBeenCalledWith('/routes', {
        params: { skip: 0, limit: 5 }
      })
    })

    it('should use default pagination values', async () => {
      const mockResponse = {
        data: {
          total: 5,
          items: []
        }
      }

      mockedAxios.get.mockResolvedValue(mockResponse)

      await fetchRoutes()

      expect(mockedAxios.get).toHaveBeenCalledWith('/routes', {
        params: { skip: 0, limit: 10 }
      })
    })
  })

  describe('fetchRouteDetails', () => {
    it('should fetch route details with locations_sequence and locations_data', async () => {
      const mockRouteDetails = {
        id: 'route-123',
        name: 'Test Route',
        locations: ['loc-1', 'loc-2'],
        locations_sequence: ['loc-2', 'loc-1'],
        locations_data: [
          {
            id: 'loc-1',
            name: 'Store 1',
            latitude: 55.7558,
            longitude: 37.6173,
            address: 'Address 1',
            time_window_start: '09:00',
            time_window_end: '18:00',
            priority: 1
          },
          {
            id: 'loc-2',
            name: 'Store 2',
            latitude: 55.7489,
            longitude: 37.616,
            address: 'Address 2',
            time_window_start: '09:00',
            time_window_end: '18:00',
            priority: 2
          }
        ],
        total_distance_km: 25.5,
        total_time_hours: 2.5,
        total_cost_rub: 1500,
        model_used: 'qwen',
        fallback_reason: null,
        created_at: '2026-02-13T10:30:00Z'
      }

      mockedAxios.get.mockResolvedValue({ data: mockRouteDetails })

      const result = await fetchRouteDetails('route-123')

      expect(result.id).toBe('route-123')
      expect(result.locations_sequence).toBeDefined()
      expect(result.locations_sequence).toHaveLength(2)
      expect(result.locations_data).toBeDefined()
      expect(result.locations_data).toHaveLength(2)
      expect(mockedAxios.get).toHaveBeenCalledWith('/routes/route-123')
    })
  })

  describe('fetchRouteMetrics', () => {
    it('should fetch metrics for specific route', async () => {
      const mockMetrics = {
        metrics: [
          {
            id: 'metric-1',
            route_id: 'route-123',
            model: 'llama',
            response_time_ms: 1245,
            quality_score: 0.87,
            cost_rub: 25.5,
            timestamp: '2026-02-13T09:15:30Z'
          }
        ]
      }

      mockedAxios.get.mockResolvedValue({ data: mockMetrics })

      const result = await fetchRouteMetrics('route-123')

      expect(result.metrics).toHaveLength(1)
      expect(result.metrics[0].route_id).toBe('route-123')
      expect(mockedAxios.get).toHaveBeenCalledWith('/metrics', {
        params: { route_id: 'route-123' }
      })
    })
  })

  describe('runBenchmark', () => {
    it('should run benchmark with provided locations', async () => {
      const mockRequest = {
        test_locations: [
          {
            id: 'loc-1',
            name: 'Store 1',
            latitude: 55.7558,
            longitude: 37.6173
          }
        ],
        num_iterations: 5
      }

      const mockResponse = {
        data: {
          total_duration_seconds: 45.2,
          results: [
            {
              model: 'llama',
              num_tests: 5,
              avg_response_time_ms: 1250,
              min_response_time_ms: 850,
              max_response_time_ms: 2100,
              avg_quality_score: 0.87,
              total_cost_rub: 250,
              success_rate: 1.0,
              timestamp: '2026-02-13T11:00:00Z'
            }
          ]
        }
      }

      mockedAxios.post.mockResolvedValue(mockResponse)

      const result = await runBenchmark(mockRequest)

      expect(result.total_duration_seconds).toBe(45.2)
      expect(result.results).toHaveLength(1)
      expect(mockedAxios.post).toHaveBeenCalledWith('/benchmark', mockRequest)
    })
  })

  describe('checkHealth', () => {
    it('should return health status when service is healthy', async () => {
      const mockHealth = {
        status: 'healthy',
        services: {
          database: 'connected',
          qwen: 'available',
          llama: 'connected'
        }
      }

      mockedAxios.get.mockResolvedValue({ data: mockHealth })

      const result = await checkHealth()

      expect(result.status).toBe('healthy')
      expect(result.services.database).toBe('connected')
      expect(mockedAxios.get).toHaveBeenCalledWith('/health')
    })

    it('should handle 503 service unavailable', async () => {
      const mockUnhealthy = {
        status: 'unhealthy',
        services: {
          database: 'connected',
          qwen: 'unavailable',
          llama: 'available'
        }
      }

      const errorResponse = {
        response: {
          status: 503,
          data: mockUnhealthy
        }
      }

      mockedAxios.get.mockRejectedValue(errorResponse)

      const result = await checkHealth()

      expect(result.status).toBe('unhealthy')
      expect(result.services.qwen).toBe('unavailable')
    })
  })

  describe('fetchAllLocations', () => {
    it('should fetch all locations', async () => {
      const mockLocations = [
        {
          id: 'loc-1',
          name: 'Store 1',
          latitude: 55.7558,
          longitude: 37.6173,
          address: 'Address 1',
          time_window_start: '09:00',
          time_window_end: '18:00',
          priority: 1
        },
        {
          id: 'loc-2',
          name: 'Store 2',
          latitude: 55.7489,
          longitude: 37.616,
          address: 'Address 2',
          time_window_start: '10:00',
          time_window_end: '19:00',
          priority: 2
        }
      ]

      mockedAxios.get.mockResolvedValue({ data: mockLocations })

      const result = await fetchAllLocations()

      expect(result).toHaveLength(2)
      expect(mockedAxios.get).toHaveBeenCalledWith('/locations')
    })
  })

  describe('retry logic', () => {
    it('should retry on 5xx errors', async () => {
      const errorResponse = {
        response: {
          status: 500,
          data: { error: 'Server Error' }
        }
      }

      const successResponse = { data: { metrics: [] } }

      mockedAxios.get
        .mockRejectedValueOnce(errorResponse)
        .mockRejectedValueOnce(errorResponse)
        .mockResolvedValueOnce(successResponse)

      const result = await getMetrics()

      expect(result).toBeDefined()
      expect(mockedAxios.get).toHaveBeenCalledTimes(3)
    })

    it('should not retry on 4xx errors', async () => {
      const errorResponse = {
        response: {
          status: 400,
          data: { error: 'Bad Request' }
        }
      }

      mockedAxios.get.mockRejectedValue(errorResponse)

      try {
        await getMetrics()
        expect.fail('Should have thrown an error')
      } catch (error) {
        expect(mockedAxios.get).toHaveBeenCalledTimes(1)
      }
    })

    it('should not retry on network errors', async () => {
      const errorResponse = {
        code: 'ECONNABORTED',
        message: 'timeout'
      }

      mockedAxios.get.mockRejectedValue(errorResponse)

      try {
        await getMetrics()
        expect.fail('Should have thrown an error')
      } catch (error) {
        expect(mockedAxios.get).toHaveBeenCalledTimes(1)
      }
    })
  })
})
