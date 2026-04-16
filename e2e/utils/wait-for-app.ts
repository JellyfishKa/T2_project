/**
 * Poll /health until the backend responds as healthy.
 * Used in global setup before the test suite starts.
 */
export async function waitForApp(
  apiUrl = 'http://localhost:8000',
  maxWaitMs = 60_000,
  intervalMs = 1_000,
): Promise<void> {
  const deadline = Date.now() + maxWaitMs
  while (Date.now() < deadline) {
    try {
      const res = await fetch(`${apiUrl}/health`)
      if (res.ok) {
        const body = await res.json()
        if (body.status === 'healthy') return
      }
    } catch {
      // not ready yet
    }
    await new Promise((r) => setTimeout(r, intervalMs))
  }
  throw new Error(`App did not become healthy within ${maxWaitMs}ms`)
}
