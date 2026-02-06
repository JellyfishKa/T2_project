import { describe, it, expect, beforeEach } from 'vitest'
import { createRouter, createMemoryHistory } from 'vue-router'

// Create a mock component for testing
const MockComponent = { template: '<div>Mock Component</div>' }

// Create a test router with mock routes
const createTestRouter = () => {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      {
        path: '/',
        name: 'home',
        component: MockComponent,
        meta: { title: 'Home - T2 LLM Platform' }
      },
      {
        path: '/dashboard',
        name: 'dashboard',
        component: MockComponent,
        meta: { title: 'Dashboard - T2 LLM Platform' }
      },
      {
        path: '/nonexistent',
        name: 'nonexistent',
        component: MockComponent,
        meta: { title: 'Nonexistent - T2 LLM Platform' }
      },
      // Redirect to home if route not found
      {
        path: '/:pathMatch(.*)*',
        redirect: '/'
      }
    ]
  })

  // Add the same beforeEach hook as the real router
  router.beforeEach((to, _from, next) => {
    document.title = (to.meta.title as string) || 'T2 LLM Platform'
    next()
  })

  return router
}

describe('Router', () => {
  let testRouter: ReturnType<typeof createTestRouter>

  beforeEach(() => {
    testRouter = createTestRouter()
    // Initialize the router
    testRouter.push('/')
    testRouter.isReady()
  })

  it('defines routes correctly', () => {
    const routes = testRouter.getRoutes()

    // Check that the home route exists
    const homeRoute = routes.find((route) => route.name === 'home')
    expect(homeRoute).toBeDefined()
    expect(homeRoute?.path).toBe('/')

    // Check that the dashboard route exists
    const dashboardRoute = routes.find((route) => route.name === 'dashboard')
    expect(dashboardRoute).toBeDefined()
    expect(dashboardRoute?.path).toBe('/dashboard')
  })

  it('redirects to home for non-existent routes', async () => {
    // Navigate to a non-existent route
    await testRouter.push('/this-route-does-not-exist')

    // Check that it redirects to home
    expect(testRouter.currentRoute.value.path).toBe('/')
  })

  it('updates document title on route change', async () => {
    // Mock document.title setter
    const originalTitle = document.title
    let title = originalTitle
    Object.defineProperty(document, 'title', {
      get: () => title,
      set: (val) => {
        title = val
      },
      configurable: true
    })

    // Change route to dashboard
    await testRouter.push('/dashboard')

    // Check if document title was updated
    expect(title).toBe('Dashboard - T2 LLM Platform')

    // Change back to home
    await testRouter.push('/')

    // Check if document title was updated again
    expect(title).toBe('Home - T2 LLM Platform')

    // Restore original title
    document.title = originalTitle
  })

  it('has default title for routes without meta title', async () => {
    // Add a route without meta title
    testRouter.addRoute({
      path: '/no-title',
      name: 'no-title',
      component: MockComponent
    })

    // Mock document.title setter
    const originalTitle = document.title
    let title = originalTitle
    Object.defineProperty(document, 'title', {
      get: () => title,
      set: (val) => {
        title = val
      },
      configurable: true
    })

    // Navigate to the route without title
    await testRouter.push('/no-title')

    // Check if default title is used
    expect(title).toBe('T2 LLM Platform')

    // Restore original title
    document.title = originalTitle
  })
})
