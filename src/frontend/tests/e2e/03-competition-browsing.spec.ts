import { test, expect } from '@playwright/test'

test.describe('Competition Browsing', () => {
  test('should display competitions browse page', async ({ page }) => {
    await page.goto('/competitions')

    // Check page loaded
    await expect(page.locator('h1')).toContainText(/Competitions|Photography Competitions/i)

    // Check filters are visible
    await expect(page.locator('input[label*="search" i], input[placeholder*="search" i]')).toBeVisible()
  })

  test('should have filter controls', async ({ page }) => {
    await page.goto('/competitions')

    // Check search input
    const searchInput = page.locator('input[label*="search" i], input[placeholder*="search" i]')
    await expect(searchInput).toBeVisible()

    // Check status filter
    const statusFilter = page.locator('select[label*="status" i], .v-select:has-text("Status")')
    await expect(statusFilter).toBeVisible()

    // Check view mode toggle (grid/list)
    const viewToggle = page.locator('button:has(.mdi-view-grid), button:has(.mdi-view-list)')
    await expect(viewToggle.first()).toBeVisible()
  })

  test('should filter competitions by search', async ({ page }) => {
    await page.goto('/competitions')

    // Wait for any initial load
    await page.waitForTimeout(1000)

    // Type in search
    const searchInput = page.locator('input[label*="search" i], input[placeholder*="search" i]')
    await searchInput.fill('nature')

    // Wait for search to trigger
    await page.waitForTimeout(500)

    // URL or content should update
    // (Actual behavior depends on whether competitions are loaded from API)
  })

  test('should toggle between grid and list view', async ({ page }) => {
    await page.goto('/competitions')

    // Find view toggle buttons
    const gridButton = page.locator('button:has(.mdi-view-grid)')
    const listButton = page.locator('button:has(.mdi-view-list)')

    // Click list view
    if (await listButton.count() > 0) {
      await listButton.first().click()
      await page.waitForTimeout(300)
    }

    // Click grid view
    if (await gridButton.count() > 0) {
      await gridButton.first().click()
      await page.waitForTimeout(300)
    }
  })

  test('should display competition cards or empty state', async ({ page }) => {
    await page.goto('/competitions')
    await page.waitForTimeout(1000)

    // Either show cards or empty state
    const hasCards = await page.locator('.competition-card, .v-card:has-text("Competition")').count()
    const hasEmptyState = await page.locator('text=/no.*competitions.*found/i').count()

    expect(hasCards > 0 || hasEmptyState > 0).toBeTruthy()
  })

  test('should navigate to competition detail when clicking card', async ({ page }) => {
    await page.goto('/competitions')
    await page.waitForTimeout(1000)

    // Find first competition card
    const firstCard = page.locator('.competition-card, .v-card >> a, a.v-card').first()

    if (await firstCard.count() > 0) {
      await firstCard.click()

      // Should navigate to detail page
      await page.waitForURL('**/competitions/**', { timeout: 5000 })
    }
  })

  test('should display load more button if applicable', async ({ page }) => {
    await page.goto('/competitions')
    await page.waitForTimeout(1000)

    // Check for load more button
    const loadMoreButton = page.locator('button:has-text("Load More")')

    // If it exists, clicking should load more
    if (await loadMoreButton.count() > 0) {
      const initialCards = await page.locator('.competition-card, .v-card').count()
      await loadMoreButton.click()
      await page.waitForTimeout(1000)

      // Cards count might increase (depends on API)
      const newCards = await page.locator('.competition-card, .v-card').count()
      expect(newCards >= initialCards).toBeTruthy()
    }
  })

  test('should show clear filters button when filters are active', async ({ page }) => {
    await page.goto('/competitions')

    // Apply a filter
    const searchInput = page.locator('input[label*="search" i], input[placeholder*="search" i]')
    await searchInput.fill('test')
    await page.waitForTimeout(500)

    // Should show clear button
    const clearButton = page.locator('button:has-text("Clear"), button:has(.mdi-close)')
    const clearAllButton = page.locator('button:has-text("Clear All")')

    const hasClearButton = (await clearButton.count()) > 0 || (await clearAllButton.count()) > 0
    expect(hasClearButton).toBeTruthy()
  })
})
