import { test, expect } from '@playwright/test'

test.describe('Navigation', () => {
  test('should have correct navigation menu items for guest users', async ({ page }) => {
    await page.goto('/')

    // Check for main navigation items
    await expect(page.getByRole('link', { name: /^a\.v\.a\.r\.$/i })).toBeVisible()
    await expect(page.getByRole('link', { name: /^competitions$/i })).toBeVisible()

    // Check for auth buttons
    await expect(page.getByRole('link', { name: /sign in/i })).toBeVisible()
    await expect(page.getByRole('link', { name: /sign up/i })).toBeVisible()
  })

  test('should navigate to home from logo', async ({ page }) => {
    await page.goto('/competitions')

    await page.getByRole('link', { name: /^a\.v\.a\.r\.$/i }).click()
    await expect(page).toHaveURL('/')
  })

  test('should have working footer links', async ({ page }) => {
    await page.goto('/')

    // Check footer exists
    await expect(page.locator('footer')).toBeVisible()
    await expect(page.getByText(/© 2024 A\.V\.A\.R\./i)).toBeVisible()
  })

  test('should navigate between all main pages', async ({ page }) => {
    // Start at home
    await page.goto('/')
    await expect(page.getByRole('heading', { name: /a\.v\.a\.r\./i })).toBeVisible()

    // Go to competitions
    await page.getByRole('link', { name: /browse competitions/i }).first().click()
    await expect(page).toHaveURL(/\/competitions/)

    // Go back to home
    await page.getByRole('link', { name: /^a\.v\.a\.r\.$/i }).click()
    await expect(page).toHaveURL('/')

    // Go to login
    await page.getByRole('link', { name: /sign in/i }).first().click()
    await expect(page).toHaveURL(/\/login/)

    // Go to register
    await page.getByRole('link', { name: /sign up/i }).click()
    await expect(page).toHaveURL(/\/register/)
  })

  test('should have responsive navigation', async ({ page }) => {
    await page.goto('/')

    // Check navigation container exists
    const header = page.locator('header')
    await expect(header).toBeVisible()

    // Check it has the sticky positioning
    await expect(header).toHaveCSS('position', 'sticky')
  })
})
