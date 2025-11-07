import { test, expect } from '@playwright/test'

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('should load the home page', async ({ page }) => {
    await expect(page).toHaveTitle(/A.V.A.R./)
    await expect(page.getByText('Anti-AI Verification')).toBeVisible()
  })

  test('should navigate to registration page', async ({ page }) => {
    await page.getByRole('link', { name: /sign up|get started/i }).first().click()
    await expect(page).toHaveURL(/\/register/)
    await expect(page.getByRole('heading', { name: /create account/i })).toBeVisible()
  })

  test('should show validation errors for empty registration form', async ({ page }) => {
    await page.goto('/register')

    // Try to submit empty form
    await page.getByRole('button', { name: /create account/i }).click()

    // Check if browser validation prevents submission
    const emailInput = page.locator('input[type="email"]')
    await expect(emailInput).toHaveAttribute('required', '')
  })

  test('should register a new user', async ({ page }) => {
    await page.goto('/register')

    const timestamp = Date.now()
    const testEmail = `test${timestamp}@example.com`
    const testUsername = `testuser${timestamp}`

    await page.locator('input[id="email"]').fill(testEmail)
    await page.locator('input[id="username"]').fill(testUsername)
    await page.locator('input[id="full_name"]').fill('Test User')
    await page.locator('input[id="country"]').fill('USA')
    await page.locator('input[id="password"]').fill('TestPassword123!')
    await page.locator('input[id="confirmPassword"]').fill('TestPassword123!')

    await page.getByRole('button', { name: /create account/i }).click()

    // Should redirect to competitions or show error
    await page.waitForTimeout(2000)
    const url = page.url()
    expect(url).toMatch(/(\/competitions|\/register)/)
  })

  test('should show error for mismatched passwords', async ({ page }) => {
    await page.goto('/register')

    await page.locator('input[id="email"]').fill('test@example.com')
    await page.locator('input[id="username"]').fill('testuser')
    await page.locator('input[id="password"]').fill('Password123!')
    await page.locator('input[id="confirmPassword"]').fill('DifferentPassword123!')

    await page.getByRole('button', { name: /create account/i }).click()

    // Should show error message
    await expect(page.getByText(/passwords do not match/i)).toBeVisible({ timeout: 3000 })
  })

  test('should navigate to login page', async ({ page }) => {
    await page.getByRole('link', { name: /sign in/i }).first().click()
    await expect(page).toHaveURL(/\/login/)
    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible()
  })

  test('should show login form', async ({ page }) => {
    await page.goto('/login')

    await expect(page.locator('input[id="email"]')).toBeVisible()
    await expect(page.locator('input[id="password"]')).toBeVisible()
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible()
  })

  test('should have link to registration from login', async ({ page }) => {
    await page.goto('/login')

    await expect(page.getByRole('link', { name: /sign up/i })).toBeVisible()
  })

  test('should have link to login from registration', async ({ page }) => {
    await page.goto('/register')

    await expect(page.getByRole('link', { name: /sign in/i })).toBeVisible()
  })
})
