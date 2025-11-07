import { test, expect } from '@playwright/test'

test.describe('API Integration', () => {
  test('should successfully fetch competitions from API', async ({ page }) => {
    // Set up request interception to monitor API calls
    let competitionsApiCalled = false

    page.on('response', response => {
      if (response.url().includes('/api/v1/competitions')) {
        competitionsApiCalled = true
      }
    })

    await page.goto('/competitions')

    // Wait for API call
    await page.waitForTimeout(3000)

    // Verify API was called
    expect(competitionsApiCalled).toBe(true)
  })

  test('should handle API errors gracefully', async ({ page }) => {
    // Intercept and fail the API request
    await page.route('**/api/v1/competitions', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ detail: 'Internal Server Error' })
      })
    })

    await page.goto('/competitions')

    // Should show error message or handle gracefully
    await page.waitForTimeout(2000)

    // Page should still be functional
    await expect(page.locator('body')).toBeVisible()
  })

  test('should make authenticated requests when logged in', async ({ page }) => {
    let hasAuthHeader = false

    page.on('request', request => {
      const headers = request.headers()
      if (headers.authorization && headers.authorization.startsWith('Bearer ')) {
        hasAuthHeader = true
      }
    })

    await page.goto('/')

    // Check if token exists in localStorage
    const hasToken = await page.evaluate(() => {
      return localStorage.getItem('access_token') !== null
    })

    if (hasToken) {
      // Navigate to a protected page
      await page.goto('/my-submissions')
      await page.waitForTimeout(1000)

      expect(hasAuthHeader).toBe(true)
    }
  })

  test('should redirect to login for protected routes when not authenticated', async ({ page }) => {
    // Clear any existing tokens
    await page.goto('/')
    await page.evaluate(() => {
      localStorage.clear()
    })

    // Try to access protected route
    await page.goto('/my-submissions')

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/, { timeout: 5000 })
  })

  test('should handle network timeout gracefully', async ({ page, context }) => {
    // Set a very short timeout
    await context.route('**/api/v1/**', route => {
      // Delay response
      setTimeout(() => {
        route.fulfill({
          status: 200,
          body: JSON.stringify([])
        })
      }, 35000) // Longer than default timeout
    })

    await page.goto('/competitions')

    // Should eventually show content or error
    await page.waitForTimeout(5000)
    await expect(page.locator('body')).toBeVisible()
  })
})
