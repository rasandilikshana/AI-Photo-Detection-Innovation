import { test, expect, Page } from '@playwright/test';

// Test configuration
const BASE_URL = 'http://localhost:5173';
const API_URL = 'http://localhost:8080';

// Helper to generate unique data for each test run
function uniqueEmail() {
  return `test_${Date.now()}_${Math.random().toString(36).substring(7)}@example.com`;
}

function uniqueUsername() {
  return `user_${Date.now()}_${Math.random().toString(36).substring(7)}`;
}

test.describe('A.V.A.R. End-to-End Tests', () => {

  test.describe('Navigation and UI', () => {
    test('should load home page with A.V.A.R. heading', async ({ page }) => {
      await page.goto(BASE_URL);

      // Check main heading is visible - the H1 contains "A.V.A.R."
      const heading = page.locator('h1');
      await expect(heading).toBeVisible();
      await expect(heading).toContainText('A.V.A.R');
    });

    test('should navigate to competitions page', async ({ page }) => {
      await page.goto(BASE_URL);

      // Click on competitions link
      await page.click('text=Competitions');
      await expect(page).toHaveURL(/.*competitions/);

      // Verify competitions page loads
      await expect(page.locator('h1')).toContainText(/Competition/i);
    });

    test('should have working Sign In link', async ({ page }) => {
      await page.goto(BASE_URL);

      // Click Sign In button/link
      await page.click('text=Sign In');
      await expect(page).toHaveURL(/.*login/);
    });

    test('should have working Sign Up link', async ({ page }) => {
      await page.goto(BASE_URL);

      // Navigate to register via Sign Up
      await page.click('text=Sign Up');
      await expect(page).toHaveURL(/.*register/);
    });

    test('should have Get Started button linking to register', async ({ page }) => {
      await page.goto(BASE_URL);

      // Click Get Started button on home page
      await page.click('text=Get Started');
      await expect(page).toHaveURL(/.*register/);
    });
  });

  test.describe('Authentication Flow', () => {
    test('should show validation errors for empty registration form', async ({ page }) => {
      await page.goto(`${BASE_URL}/register`);

      // Try to submit empty form
      await page.click('button[type="submit"]');

      // Should show validation or stay on page
      await expect(page).toHaveURL(/.*register/);
    });

    test('should register a new user successfully', async ({ page }) => {
      await page.goto(`${BASE_URL}/register`);

      const email = uniqueEmail();
      const username = uniqueUsername();
      const password = 'TestPassword123!';

      // Fill registration form - use specific IDs
      await page.fill('input#email', email);
      await page.fill('input#username', username);
      await page.fill('input#full_name', 'Test User');
      await page.fill('input#password', password);
      await page.fill('input#confirmPassword', password);

      // Submit form
      await page.click('button[type="submit"]');

      // Wait for navigation
      await page.waitForTimeout(3000);

      // Should redirect to competitions page after successful registration
      const currentUrl = page.url();
      expect(currentUrl.includes('competitions') || currentUrl.includes('login') || currentUrl === BASE_URL + '/').toBeTruthy();
    });

    test('should login with valid credentials', async ({ page }) => {
      // First register a user
      await page.goto(`${BASE_URL}/register`);

      const email = uniqueEmail();
      const username = uniqueUsername();
      const password = 'TestPassword123!';

      // Fill registration form with confirmPassword
      await page.fill('input#email', email);
      await page.fill('input#username', username);
      await page.fill('input#password', password);
      await page.fill('input#confirmPassword', password);
      await page.click('button[type="submit"]');

      await page.waitForTimeout(3000);

      // Now login
      await page.goto(`${BASE_URL}/login`);
      await page.fill('input#email', email);
      await page.fill('input#password', password);
      await page.click('button[type="submit"]');

      // Wait for login to complete
      await page.waitForTimeout(3000);

      // Should be redirected away from login page
      await expect(page).not.toHaveURL(/.*login/);
    });

    test('should show error for invalid login', async ({ page }) => {
      await page.goto(`${BASE_URL}/login`);

      await page.fill('input[type="email"]', 'nonexistent@example.com');
      await page.fill('input[type="password"]', 'WrongPassword123!');
      await page.click('button[type="submit"]');

      // Should show error message
      await page.waitForTimeout(1000);

      // Check for error alert or stay on login page
      const errorAlert = page.locator('[role="alert"], .error, .text-red-500, .text-destructive');
      const isOnLoginPage = page.url().includes('login');

      expect(await errorAlert.count() > 0 || isOnLoginPage).toBeTruthy();
    });
  });

  test.describe('Competitions', () => {
    test('should display competitions list', async ({ page }) => {
      await page.goto(`${BASE_URL}/competitions`);

      // Wait for page to load
      await page.waitForTimeout(1000);

      // Check page title or heading
      await expect(page.locator('h1, h2')).toContainText(/Competition/i);
    });

    test('should be able to view competition details', async ({ page }) => {
      await page.goto(`${BASE_URL}/competitions`);

      // Wait for competitions to load
      await page.waitForTimeout(2000);

      // Try to click on a competition card or link
      const competitionLink = page.locator('a[href*="/competitions/"], [data-testid="competition-card"]').first();

      if (await competitionLink.count() > 0) {
        await competitionLink.click();
        await page.waitForTimeout(1000);

        // Should be on competition detail page
        expect(page.url()).toMatch(/\/competitions\/\d+|\/competitions\/[\w-]+/);
      }
    });
  });

  test.describe('Authenticated User Actions', () => {
    let authenticatedPage: Page;
    let userEmail: string;
    let userPassword: string;

    test.beforeAll(async ({ browser }) => {
      authenticatedPage = await browser.newPage();

      userEmail = uniqueEmail();
      const username = uniqueUsername();
      userPassword = 'TestPassword123!';

      // Register with all required fields including confirmPassword
      await authenticatedPage.goto(`${BASE_URL}/register`);
      await authenticatedPage.fill('input#email', userEmail);
      await authenticatedPage.fill('input#username', username);
      await authenticatedPage.fill('input#password', userPassword);
      await authenticatedPage.fill('input#confirmPassword', userPassword);
      await authenticatedPage.click('button[type="submit"]');
      await authenticatedPage.waitForTimeout(3000);

      // Login
      await authenticatedPage.goto(`${BASE_URL}/login`);
      await authenticatedPage.fill('input#email', userEmail);
      await authenticatedPage.fill('input#password', userPassword);
      await authenticatedPage.click('button[type="submit"]');
      await authenticatedPage.waitForTimeout(3000);
    });

    test.afterAll(async () => {
      await authenticatedPage.close();
    });

    test('should access my submissions page when logged in', async () => {
      await authenticatedPage.goto(`${BASE_URL}/my-submissions`);
      await authenticatedPage.waitForTimeout(1000);

      // Should not redirect to login
      expect(authenticatedPage.url()).toContain('submissions');
    });

    test('should hide Sign In when logged in', async () => {
      await authenticatedPage.goto(BASE_URL);
      await authenticatedPage.waitForTimeout(1000);

      // When logged in, Sign In button should NOT be visible
      const signInButton = authenticatedPage.locator('text=Sign In');
      await expect(signInButton).toBeHidden({ timeout: 5000 });
    });
  });

  test.describe('Protected Routes', () => {
    test('should redirect to login when accessing submissions without auth', async ({ page }) => {
      // Clear any existing auth
      await page.goto(BASE_URL);
      await page.evaluate(() => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      });

      // Try to access protected route
      await page.goto(`${BASE_URL}/my-submissions`);
      await page.waitForTimeout(1000);

      // Should redirect to login
      expect(page.url()).toContain('login');
    });

    test('should redirect to login when accessing submission form without auth', async ({ page }) => {
      await page.goto(BASE_URL);
      await page.evaluate(() => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      });

      await page.goto(`${BASE_URL}/submit/1`);
      await page.waitForTimeout(1000);

      expect(page.url()).toContain('login');
    });
  });

  test.describe('Responsive Design', () => {
    test('should work on mobile viewport', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto(BASE_URL);

      // Page should load and main content should be visible
      await expect(page.locator('h1')).toBeVisible();

      // Body should not overflow horizontally (with small tolerance)
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      const viewportWidth = await page.evaluate(() => window.innerWidth);
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 50);
    });

    test('should work on tablet viewport', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.goto(BASE_URL);

      await expect(page.locator('body')).toBeVisible();
      await expect(page.locator('h1')).toContainText('A.V.A.R');
    });

    test('should work on desktop viewport', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto(BASE_URL);

      await expect(page.locator('body')).toBeVisible();
      await expect(page.locator('h1')).toContainText('A.V.A.R');
    });
  });

  test.describe('API Health Checks', () => {
    test('should have healthy competition service', async ({ request }) => {
      const response = await request.get(`${API_URL}/health`);
      expect(response.ok()).toBeTruthy();

      const body = await response.json();
      expect(body.status).toBe('healthy');
    });

    test('should have accessible API root', async ({ request }) => {
      const response = await request.get(`${API_URL}/`);
      expect(response.ok()).toBeTruthy();

      const body = await response.json();
      expect(body.service).toContain('A.V.A.R');
    });

    test('should return API documentation', async ({ request }) => {
      const response = await request.get(`${API_URL}/docs`);
      expect(response.ok()).toBeTruthy();
    });
  });

  test.describe('Form Validation', () => {
    test('registration should validate email format', async ({ page }) => {
      await page.goto(`${BASE_URL}/register`);

      // Enter invalid email
      await page.fill('input[type="email"]', 'invalid-email');
      await page.fill('input[id="username"], input[name="username"]', 'testuser');
      await page.fill('input[type="password"]', 'TestPassword123!');

      await page.click('button[type="submit"]');
      await page.waitForTimeout(500);

      // Should stay on register page or show error
      expect(page.url()).toContain('register');
    });

    test('login should validate required fields', async ({ page }) => {
      await page.goto(`${BASE_URL}/login`);

      // Try to submit with empty fields
      await page.click('button[type="submit"]');
      await page.waitForTimeout(500);

      // Should stay on login page
      expect(page.url()).toContain('login');
    });
  });
});
