import { test, expect } from '@playwright/test'

test.describe('Competitions', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('should navigate to competitions page', async ({ page }) => {
    await page.getByRole('link', { name: /browse competitions/i }).first().click()
    await expect(page).toHaveURL(/\/competitions/)
    await expect(page.getByRole('heading', { name: /photography competitions/i })).toBeVisible()
  })

  test('should display competitions list', async ({ page }) => {
    await page.goto('/competitions')

    // Should show either competitions or a message
    const loadingText = page.getByText(/loading competitions/i)
    const noCompetitionsText = page.getByText(/no active competitions/i)
    const competitionsExist = page.locator('[class*="grid"]').first()

    await expect(
      loadingText.or(noCompetitionsText).or(competitionsExist)
    ).toBeVisible({ timeout: 5000 })
  })

  test('should show competition cards with required information', async ({ page }) => {
    await page.goto('/competitions')

    // Wait for page to load
    await page.waitForTimeout(2000)

    // Check if competitions are displayed
    const cards = page.locator('[class*="card"]')
    const count = await cards.count()

    if (count > 0) {
      // Check first competition card has required elements
      const firstCard = cards.first()
      await expect(firstCard).toBeVisible()

      // Check for View Details button
      const viewButton = firstCard.getByRole('button', { name: /view details/i })
      await expect(viewButton).toBeVisible()
    }
  })

  test('should navigate from home to competitions via navigation menu', async ({ page }) => {
    await page.goto('/')

    // Click on Competitions in the navigation
    await page.getByRole('link', { name: /^competitions$/i }).click()
    await expect(page).toHaveURL(/\/competitions/)
  })

  test('should handle loading state', async ({ page }) => {
    await page.goto('/competitions')

    // Should show loading or content
    const loadingIndicator = page.getByText(/loading/i)
    const content = page.locator('main')

    await expect(content).toBeVisible({ timeout: 10000 })
  })
})
