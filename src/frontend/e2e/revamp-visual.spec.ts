import { test, expect, type Page } from '@playwright/test'

const SHOTS = process.env.REVAMP_SHOTS_DIR || 'test-results/revamp-shots'

const consoleErrors: string[] = []

function watchConsole(page: Page, label: string) {
  page.on('console', (msg) => {
    if (msg.type() === 'error' && !msg.text().includes('favicon')) {
      consoleErrors.push(`[${label}] ${msg.text()}`)
    }
  })
  page.on('pageerror', (err) => {
    consoleErrors.push(`[${label}] PAGEERROR ${err.message}`)
  })
}

async function login(page: Page, email: string, password: string) {
  await page.goto('/login')
  await page.locator('#email').fill(email)
  await page.locator('#password').fill(password)
  await page.getByRole('button', { name: /sign in/i }).click()
  await page.waitForURL(/\/competitions/, { timeout: 10000 })
}

test.describe('Revamp visual regression', () => {
  test('guest: home, competitions, detail, login, register', async ({ page }) => {
    watchConsole(page, 'guest')
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await page.screenshot({ path: `${SHOTS}/01-home.png`, fullPage: true })

    await page.goto('/competitions')
    await page.waitForLoadState('networkidle')
    await page.screenshot({ path: `${SHOTS}/02-competitions.png`, fullPage: true })

    const viewButtons = page.getByRole('button', { name: /view details/i })
    if (await viewButtons.count()) {
      await viewButtons.first().click()
      await page.waitForLoadState('networkidle')
      await page.screenshot({ path: `${SHOTS}/03-competition-detail.png`, fullPage: true })
    }

    await page.goto('/login')
    await page.screenshot({ path: `${SHOTS}/04-login.png`, fullPage: true })
    await page.goto('/register')
    await page.screenshot({ path: `${SHOTS}/05-register.png`, fullPage: true })
  })

  test('judge: dashboard and competition view', async ({ page }) => {
    watchConsole(page, 'judge')
    await login(page, 'judge@avar.com', 'Judge@123!')

    await page.goto('/judge')
    await page.waitForLoadState('networkidle')
    await page.screenshot({ path: `${SHOTS}/06-judge-dashboard.png`, fullPage: true })

    const assignmentButtons = page.getByRole('button', { name: /view submissions/i })
    if (await assignmentButtons.count()) {
      await assignmentButtons.first().click()
      await page.waitForLoadState('networkidle')
      await page.screenshot({ path: `${SHOTS}/07-judge-competition.png`, fullPage: true })

      const scoreButtons = page.getByRole('button', { name: /score this entry|view details|view full details/i })
      if (await scoreButtons.count()) {
        await scoreButtons.first().click()
        await page.waitForLoadState('networkidle')
        await page.screenshot({ path: `${SHOTS}/08-score-submission.png`, fullPage: true })
      }
    }
  })

  test('organizer: panel tabs', async ({ page }) => {
    watchConsole(page, 'organizer')
    await login(page, 'organizer@avar.com', 'Organizer@123!')

    await page.goto('/organizer')
    await page.waitForLoadState('networkidle')
    await page.screenshot({ path: `${SHOTS}/09-organizer-create.png`, fullPage: true })

    await page.getByRole('button', { name: /my competitions/i }).click()
    await page.waitForLoadState('networkidle')
    await page.screenshot({ path: `${SHOTS}/10-organizer-list.png`, fullPage: true })
  })

  test('admin: all panel tabs', async ({ page }) => {
    watchConsole(page, 'admin')
    await login(page, 'admin@avar.com', 'Admin@123!')

    await page.goto('/admin')
    await page.waitForLoadState('networkidle')
    await page.screenshot({ path: `${SHOTS}/11-admin-dashboard.png`, fullPage: true })

    for (const [name, file] of [
      [/users/i, '12-admin-users'],
      [/^competitions$/i, '13-admin-competitions'],
      [/assignments/i, '14-admin-judges'],
      [/audit/i, '15-admin-audit'],
      [/analytics/i, '16-admin-analytics'],
    ] as const) {
      await page.getByRole('button', { name }).first().click()
      await page.waitForTimeout(1200)
      await page.screenshot({ path: `${SHOTS}/${file}.png`, fullPage: true })
    }
  })

  test('mobile: home and menu', async ({ page }) => {
    watchConsole(page, 'mobile')
    await page.setViewportSize({ width: 375, height: 812 })
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await page.screenshot({ path: `${SHOTS}/17-mobile-home.png`, fullPage: true })

    await page.getByRole('button', { name: /open menu/i }).click()
    await page.screenshot({ path: `${SHOTS}/18-mobile-menu.png` })

    await page.setViewportSize({ width: 375, height: 812 })
    await page.goto('/register')
    await page.screenshot({ path: `${SHOTS}/19-mobile-register.png`, fullPage: true })
  })

  test.afterAll(async () => {
    if (consoleErrors.length) {
      console.log('CONSOLE ERRORS COLLECTED:\n' + consoleErrors.join('\n'))
    } else {
      console.log('NO CONSOLE ERRORS')
    }
  })
})
