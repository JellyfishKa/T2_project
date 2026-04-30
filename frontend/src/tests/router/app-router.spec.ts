import { beforeEach, describe, expect, it } from 'vitest'
import router from '@/router'

describe('App Router', () => {
  beforeEach(async () => {
    await router.push('/')
    await router.isReady()
  })

  it('redirects legacy reps route to employees tab in database view', async () => {
    await router.push('/reps')

    expect(router.currentRoute.value.path).toBe('/database')
    expect(router.currentRoute.value.query.tab).toBe('employees')
  })

  it('redirects legacy cars route to vehicles tab in database view', async () => {
    await router.push('/cars')

    expect(router.currentRoute.value.path).toBe('/database')
    expect(router.currentRoute.value.query.tab).toBe('vehicles')
  })
})
