# A.V.A.R. Testing Guide

Complete testing documentation for the A.V.A.R. platform, including Docker setup and automated browser testing.

## Table of Contents

1. [Frontend Testing](#frontend-testing)
2. [E2E Testing with Playwright](#e2e-testing-with-playwright)
3. [Docker Setup](#docker-setup)
4. [Running Tests](#running-tests)
5. [CI/CD Integration](#cicd-integration)

## Frontend Testing

### Overview

The frontend uses **Playwright** for end-to-end browser automation testing. Playwright provides:
- Cross-browser testing (Chromium, Firefox, WebKit)
- Mobile device emulation
- Automatic waiting and retry logic
- Screenshot and video capture
- Parallel test execution

### Test Structure

```
src/frontend/tests/e2e/
├── 01-navigation.spec.ts       # Navigation and routing tests
├── 02-authentication.spec.ts   # Login/register form tests
├── 03-competition-browsing.spec.ts  # Competition browsing tests
└── 04-home-page.spec.ts        # Homepage tests
```

## E2E Testing with Playwright

### Installation

Playwright is already installed as a dev dependency. To install browsers:

```bash
cd src/frontend
npx playwright install
```

This installs Chromium, Firefox, and WebKit browsers.

### Configuration

Playwright configuration is in `playwright.config.ts`:

```typescript
{
  testDir: './tests/e2e',
  timeout: 30000,
  fullyParallel: true,
  baseURL: 'http://localhost:5173',
  projects: [
    { name: 'chromium' },
    { name: 'firefox' },
    { name: 'webkit' },
    { name: 'Mobile Chrome' },
    { name: 'Mobile Safari' },
    { name: 'iPad' },
  ]
}
```

### Running Tests

#### Run all tests (headless)
```bash
npm run test:e2e
```

#### Run with UI mode (interactive)
```bash
npm run test:e2e:ui
```

#### Run in headed mode (see browser)
```bash
npm run test:e2e:headed
```

#### Run specific browser
```bash
npm run test:e2e:chromium
npm run test:e2e:firefox
npm run test:e2e:webkit
```

#### View test report
```bash
npm run test:e2e:report
```

### Test Examples

**Navigation Test:**
```typescript
test('should load the home page successfully', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveTitle(/A\.V\.A\.R/)
  await expect(page.locator('header')).toBeVisible()
})
```

**Authentication Test:**
```typescript
test('should show validation errors for empty login form', async ({ page }) => {
  await page.goto('/auth/login')
  await page.click('button[type="submit"]')
  await expect(page.locator('text=/email.*required/i')).toBeVisible()
})
```

**Competition Browsing Test:**
```typescript
test('should filter competitions by search', async ({ page }) => {
  await page.goto('/competitions')
  await page.fill('input[placeholder*="search"]', 'nature')
  await page.waitForTimeout(500)
  // Verify results updated
})
```

## Docker Setup

### Frontend Docker Configuration

#### Multi-stage Dockerfile

The frontend uses a multi-stage build:

1. **Builder Stage**: Compiles Vue app
2. **Production Stage**: Serves with nginx
3. **Development Stage**: Runs Vite dev server

```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine AS production
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80

# Development stage
FROM node:20-alpine AS development
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

### Docker Compose Setup

#### Production Frontend
```yaml
frontend:
  build:
    context: ./src/frontend
    dockerfile: Dockerfile
    target: production
  container_name: avar-frontend
  ports:
    - "3000:80"
  depends_on:
    - api-gateway
    - competition-service
  networks:
    - avar-network
```

#### Development Frontend
```yaml
frontend-dev:
  build:
    context: ./src/frontend
    dockerfile: Dockerfile
    target: development
  container_name: avar-frontend-dev
  environment:
    - VITE_API_URL=http://localhost:8080
    - VITE_AI_DETECTION_URL=http://localhost:8001
  ports:
    - "5173:5173"
  volumes:
    - ./src/frontend:/app
    - /app/node_modules
  profiles:
    - development
```

### Building and Running

#### Build production frontend
```bash
docker compose build frontend
```

#### Run production frontend
```bash
docker compose up frontend
```

Access at: http://localhost:3000

#### Run development frontend
```bash
docker compose --profile development up frontend-dev
```

Access at: http://localhost:5173

#### Run all services
```bash
docker compose up -d
```

Services:
- Frontend: http://localhost:3000
- Competition API: http://localhost:8080
- AI Detection API: http://localhost:8001
- API Gateway: http://localhost:8000

## Running Tests

### Local Development Testing

1. **Start the dev server:**
```bash
cd src/frontend
npm run dev
```

2. **Run tests (in another terminal):**
```bash
npm run test:e2e
```

The tests will automatically start the dev server if not already running.

### Docker Container Testing

To run tests against the dockerized frontend:

1. **Start frontend container:**
```bash
docker compose up frontend -d
```

2. **Run tests with custom base URL:**
```bash
cd src/frontend
PLAYWRIGHT_BASE_URL=http://localhost:3000 npx playwright test
```

### Full Stack Testing

To test with all backend services running:

1. **Start all services:**
```bash
docker compose up -d
```

2. **Wait for services to be healthy:**
```bash
docker compose ps
```

3. **Run E2E tests:**
```bash
cd src/frontend
npm run test:e2e
```

This tests the complete flow with real API calls.

## Test Scenarios Covered

### ✅ Navigation Tests (01-navigation.spec.ts)
- Home page loads successfully
- Navigation between pages
- Protected route redirects
- Footer visibility
- 404 page handling
- Responsive mobile navigation

### ✅ Authentication Tests (02-authentication.spec.ts)
- Login form display
- Register form display
- Empty form validation
- Invalid email validation
- Password strength indicator
- Password matching validation
- Password visibility toggle
- Navigation between login/register
- Terms checkbox

### ✅ Competition Browsing Tests (03-competition-browsing.spec.ts)
- Browse page display
- Filter controls
- Search functionality
- View mode toggle (grid/list)
- Competition cards or empty state
- Navigate to detail page
- Load more pagination
- Clear filters button

### ✅ Home Page Tests (04-home-page.spec.ts)
- Hero section display
- Features section
- Statistics section
- "How It Works" section
- Call-to-action section
- CTA button navigation
- Mobile responsiveness

## CI/CD Integration

### GitHub Actions Example

Create `.github/workflows/e2e-tests.yml`:

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install dependencies
        run: |
          cd src/frontend
          npm ci

      - name: Install Playwright browsers
        run: |
          cd src/frontend
          npx playwright install --with-deps

      - name: Run E2E tests
        run: |
          cd src/frontend
          npm run test:e2e

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: src/frontend/test-results/
```

## Test Reports

After running tests, view the HTML report:

```bash
npm run test:e2e:report
```

This opens an interactive report showing:
- Test results (pass/fail)
- Screenshots of failures
- Videos of test runs
- Execution timeline
- Error stack traces

## Best Practices

### 1. Use Data Test IDs
Add `data-testid` attributes for stable selectors:
```vue
<button data-testid="login-submit">Login</button>
```

```typescript
await page.click('[data-testid="login-submit"]')
```

### 2. Wait for Elements
Use Playwright's auto-waiting:
```typescript
await expect(page.locator('h1')).toBeVisible()
```

### 3. Avoid Hard-Coded Waits
Instead of:
```typescript
await page.waitForTimeout(5000) // BAD
```

Use:
```typescript
await page.waitForSelector('.competition-card') // GOOD
await expect(page.locator('.loading')).toBeHidden() // BETTER
```

### 4. Test in Isolation
Each test should be independent:
```typescript
test.beforeEach(async ({ page }) => {
  // Reset state before each test
  await page.goto('/')
})
```

### 5. Use Page Objects
For complex pages, create page objects:
```typescript
class LoginPage {
  constructor(private page: Page) {}

  async login(email: string, password: string) {
    await this.page.fill('[name="email"]', email)
    await this.page.fill('[name="password"]', password)
    await this.page.click('button[type="submit"]')
  }
}
```

## Troubleshooting

### Tests failing with timeout
- Increase timeout in `playwright.config.ts`
- Check if dev server is running
- Verify base URL is correct

### Browser not found
```bash
npx playwright install
```

### Port already in use
- Kill process on port 5173: `lsof -ti:5173 | xargs kill`
- Or change port in Vite config

### Docker container not accessible
- Check container is running: `docker compose ps`
- Verify port mapping: `docker compose port frontend 80`
- Check logs: `docker compose logs frontend`

## Summary

- **E2E Framework**: Playwright
- **Test Files**: 4 spec files, 30+ tests
- **Browsers Tested**: Chromium, Firefox, WebKit, Mobile
- **Docker**: Multi-stage build with nginx
- **Run Command**: `npm run test:e2e`
- **View Report**: `npm run test:e2e:report`

The testing setup provides comprehensive coverage of:
✅ Navigation and routing
✅ Authentication flows
✅ Form validation
✅ Competition browsing
✅ Mobile responsiveness
✅ Error handling

All tests can run locally or in Docker containers, with full CI/CD support.
