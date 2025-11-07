import { test, expect } from '@playwright/test'

test.describe('Navigation and Routing', () => {
  test('should load the home page successfully', async ({ page }) => {
    await page.goto('/')

    // Check page title
    await expect(page).toHaveTitle(/A\.V\.A\.R|Authentic Visual Art Recognition/)

    // Check header is visible
    await expect(page.locator('header')).toBeVisible()

    // Check main content loaded
    await expect(page.locator('main, .v-main')).toBeVisible()
  })

  test('should navigate between pages', async ({ page }) => {
    await page.goto('/')

    // Navigate to competitions
    await page.click('text=Competitions')
    await page.waitForURL('**/competitions')
    await expect(page.locator('h1')).toContainText('Competitions')

    // Navigate back to home
    await page.click('text=Home')
    await page.waitForURL('**/')
  })

  test('should show login page when unauthenticated user tries to access protected route', async ({ page }) => {
    await page.goto('/dashboard/participant')

    // Should redirect to login
    await page.waitForURL('**/auth/login**')
    await expect(page.locator('h1')).toContainText(/Welcome Back|Login|Sign In/i)
  })

  test('should display footer on all pages', async ({ page }) => {
    // Check on home page
    await page.goto('/')
    await expect(page.locator('footer')).toBeVisible()

    // Check on competitions page
    await page.goto('/competitions')
    await expect(page.locator('footer')).toBeVisible()
  })

  test('should handle 404 pages gracefully', async ({ page }) => {
    await page.goto('/this-page-does-not-exist')

    // Should show 404 page
    await expect(page.locator('text=404')).toBeVisible()
    await expect(page.locator('text=/Not Found|Page Not Found/i')).toBeVisible()

    // Should have "Go Back" or "Home" button
    const homeButton = page.locator('button:has-text("Home"), a:has-text("Home")')
    await expect(homeButton).toBeVisible()
  })

  test('should have responsive navigation on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/')

    // Look for hamburger menu icon
    const menuButton = page.locator('button[aria-label*="menu"], button:has(.mdi-menu)')
    await expect(menuButton).toBeVisible()

    // Click to open menu
    await menuButton.click()

    // Navigation should appear
    await expect(page.locator('nav, .v-navigation-drawer')).toBeVisible()
  })
})
