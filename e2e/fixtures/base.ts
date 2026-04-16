import { test as base, APIRequestContext } from '@playwright/test'

type Fixtures = {
  apiClient: APIRequestContext
}

export const test = base.extend<Fixtures>({
  apiClient: async ({ playwright }, use) => {
    const client = await playwright.request.newContext({
      baseURL: process.env.API_URL ?? 'http://127.0.0.1:8000',
      extraHTTPHeaders: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
    })
    await use(client)
    await client.dispose()
  },
})

export { expect } from '@playwright/test'
