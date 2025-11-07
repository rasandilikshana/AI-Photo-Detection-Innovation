import { test, expect } from '@playwright/test'

test.describe('Authentication Flow', () => {
  test('should display login form', async ({ page }) => {
    await page.goto('/auth/login')

    // Check form elements
    await expect(page.locator('h1')).toContainText(/Welcome Back|Login|Sign In/i)
    await expect(page.locator('input[type="email"], input[label*="email" i]')).toBeVisible()
    await expect(page.locator('input[type="password"], input[label*="password" i]')).toBeVisible()
    await expect(page.locator('button[type="submit"], button:has-text("Sign In")')).toBeVisible()
  })

  test('should show validation errors for empty login form', async ({ page }) => {
    await page.goto('/auth/login')

    // Try to submit empty form
    await page.click('button[type="submit"], button:has-text("Sign In")')

    // Should show validation errors
    await expect(page.locator('text=/email.*required/i, text=/password.*required/i')).toBeVisible({
      timeout: 5000,
    })
  })

  test('should show validation error for invalid email format', async ({ page }) => {
    await page.goto('/auth/login')

    // Enter invalid email
    await page.fill('input[type="email"]', 'invalid-email')
    await page.fill('input[type="password"]', 'password123')

    // Blur to trigger validation
    await page.press('input[type="password"]', 'Tab')

    // Should show email format error
    await expect(page.locator('text=/valid.*email/i')).toBeVisible({ timeout: 3000 })
  })

  test('should display register form', async ({ page }) => {
    await page.goto('/auth/register')

    // Check form elements
    await expect(page.locator('h1')).toContainText(/Create Account|Sign Up|Register/i)
    await expect(page.locator('input[label*="name" i]')).toBeVisible()
    await expect(page.locator('input[label*="username" i]')).toBeVisible()
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toHaveCount(2) // Password and confirm
  })

  test('should show password strength indicator on register', async ({ page }) => {
    await page.goto('/auth/register')

    // Fill password field
    const passwordInput = page.locator('input[type="password"]').first()
    await passwordInput.fill('weak')

    // Should show strength indicator
    await expect(page.locator('text=/strength|weak|fair|strong/i')).toBeVisible({ timeout: 3000 })
  })

  test('should validate password matching on register', async ({ page }) => {
    await page.goto('/auth/register')

    // Fill passwords with different values
    const passwordInputs = page.locator('input[type="password"]')
    await passwordInputs.nth(0).fill('MyPassword123!')
    await passwordInputs.nth(1).fill('DifferentPassword123!')
    await passwordInputs.nth(1).blur()

    // Should show mismatch error
    await expect(page.locator('text=/passwords.*match/i')).toBeVisible({ timeout: 3000 })
  })

  test('should toggle password visibility', async ({ page }) => {
    await page.goto('/auth/login')

    const passwordInput = page.locator('input[type="password"]').first()
    const toggleButton = page.locator('button:has(.mdi-eye), button:has(.mdi-eye-off)').first()

    // Password should be hidden initially
    await expect(passwordInput).toHaveAttribute('type', 'password')

    // Click toggle
    await toggleButton.click()

    // Password should now be visible
    await expect(page.locator('input[type="text"]').first()).toBeVisible()
  })

  test('should navigate between login and register', async ({ page }) => {
    await page.goto('/auth/login')

    // Click register link
    await page.click('text=/Sign Up|Register|Create.*Account/i')
    await page.waitForURL('**/auth/register')
    await expect(page.locator('h1')).toContainText(/Create Account|Sign Up|Register/i)

    // Click login link
    await page.click('text=/Sign In|Login|Already.*account/i')
    await page.waitForURL('**/auth/login')
    await expect(page.locator('h1')).toContainText(/Welcome Back|Login|Sign In/i)
  })

  test('should have terms checkbox on register', async ({ page }) => {
    await page.goto('/auth/register')

    // Look for terms checkbox
    const checkbox = page.locator('input[type="checkbox"]').first()
    await expect(checkbox).toBeVisible()

    // Should have link to terms
    await expect(page.locator('text=/terms.*service/i, a:has-text("Terms")')).toBeVisible()
  })
})
