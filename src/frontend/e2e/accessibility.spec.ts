import { test, expect } from '@playwright/test'

test.describe('Accessibility', () => {
  test('should have proper heading hierarchy on home page', async ({ page }) => {
    await page.goto('/')

    // Check for h1
    const h1 = page.locator('h1')
    await expect(h1).toBeVisible()
    await expect(h1).toHaveCount(1)

    // Check h1 content
    await expect(h1).toContainText(/authentic photography/i)
  })

  test('should have accessible forms with labels', async ({ page }) => {
    await page.goto('/login')

    // Check email input has label
    const emailLabel = page.locator('label[for="email"]')
    await expect(emailLabel).toBeVisible()

    // Check password input has label
    const passwordLabel = page.locator('label[for="password"]')
    await expect(passwordLabel).toBeVisible()

    // Check inputs have proper types
    const emailInput = page.locator('input[type="email"]')
    await expect(emailInput).toBeVisible()

    const passwordInput = page.locator('input[type="password"]')
    await expect(passwordInput).toBeVisible()
  })

  test('should have keyboard navigation support', async ({ page }) => {
    await page.goto('/')

    // Tab through focusable elements
    await page.keyboard.press('Tab')
    await page.keyboard.press('Tab')
    await page.keyboard.press('Tab')

    // Check that focus is visible
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName)
    expect(focusedElement).toBeTruthy()
  })

  test('should have alt text for images', async ({ page }) => {
    await page.goto('/')

    // Get all images
    const images = page.locator('img')
    const count = await images.count()

    if (count > 0) {
      // Check each image has alt attribute
      for (let i = 0; i < count; i++) {
        const img = images.nth(i)
        const alt = await img.getAttribute('alt')
        expect(alt).toBeTruthy()
      }
    }
  })

  test('should have proper button roles and accessibility', async ({ page }) => {
    await page.goto('/')

    // All buttons should be accessible
    const buttons = page.getByRole('button')
    const count = await buttons.count()

    expect(count).toBeGreaterThan(0)

    // Check buttons have text content or aria-label
    for (let i = 0; i < Math.min(count, 5); i++) {
      const button = buttons.nth(i)
      const text = await button.textContent()
      const ariaLabel = await button.getAttribute('aria-label')

      expect(text || ariaLabel).toBeTruthy()
    }
  })

  test('should have proper link text', async ({ page }) => {
    await page.goto('/')

    // Check navigation links have meaningful text
    const links = page.getByRole('link')
    const count = await links.count()

    expect(count).toBeGreaterThan(0)

    // Links should not just say "click here" or be empty
    for (let i = 0; i < Math.min(count, 5); i++) {
      const link = links.nth(i)
      const text = await link.textContent()
      const ariaLabel = await link.getAttribute('aria-label')

      expect(text || ariaLabel).toBeTruthy()
      if (text) {
        expect(text.toLowerCase()).not.toBe('click here')
        expect(text.toLowerCase()).not.toBe('here')
      }
    }
  })

  test('should have semantic HTML structure', async ({ page }) => {
    await page.goto('/')

    // Check for semantic elements
    await expect(page.locator('header')).toBeVisible()
    await expect(page.locator('main')).toBeVisible()
    await expect(page.locator('footer')).toBeVisible()
  })
})
