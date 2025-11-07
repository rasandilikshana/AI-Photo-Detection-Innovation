import { test, expect } from '@playwright/test'

test.describe('Home Page', () => {
  test('should display hero section', async ({ page }) => {
    await page.goto('/')

    // Check main heading
    await expect(page.locator('h1')).toContainText(/A\.V\.A\.R|Authentic|Visual|Art|Recognition/i)

    // Check CTA buttons
    const ctaButtons = page.locator('button:has-text("Browse Competitions"), button:has-text("Get Started"), a:has-text("Browse Competitions"), a:has-text("Get Started")')
    await expect(ctaButtons.first()).toBeVisible()
  })

  test('should have features section', async ({ page }) => {
    await page.goto('/')

    // Check for features section
    await expect(page.locator('text=/Why Choose|Features|AI.*Detection|Fair Competition/i')).toBeVisible()
  })

  test('should have statistics section', async ({ page }) => {
    await page.goto('/')

    // Look for stats
    const stats = page.locator('text=/10K.*Users|500.*Competitions|50K.*Submissions|99.*Accuracy/i')
    await expect(stats.first()).toBeVisible()
  })

  test('should have "How It Works" section', async ({ page }) => {
    await page.goto('/')

    // Check for how it works
    await expect(page.locator('text=/How.*Works/i')).toBeVisible()

    // Should have steps
    await expect(page.locator('text=/Create Account|Browse.*Competitions|Submit|Win/i')).toBeVisible()
  })

  test('should have call-to-action section', async ({ page }) => {
    await page.goto('/')

    // Scroll to bottom
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))

    // Check for final CTA
    await expect(page.locator('text=/Ready.*Join|Create.*Account|Get Started/i')).toBeVisible()
  })

  test('should navigate to competitions when clicking CTA', async ({ page }) => {
    await page.goto('/')

    // Click Browse Competitions button
    const browseButton = page.locator('button:has-text("Browse Competitions"), a:has-text("Browse Competitions")').first()
    await browseButton.click()

    // Should navigate to competitions page
    await page.waitForURL('**/competitions')
    await expect(page.locator('h1')).toContainText(/Competitions/i)
  })

  test('should be responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/')

    // Hero should be visible
    await expect(page.locator('h1')).toBeVisible()

    // CTA buttons should stack
    const buttons = page.locator('button:has-text("Browse"), button:has-text("Get Started")')
    await expect(buttons.first()).toBeVisible()
  })
})
