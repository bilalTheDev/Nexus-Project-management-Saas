import { test, expect } from '@playwright/test'

const email = process.env.E2E_EMAIL || 'maya@northstar.studio'
const password = process.env.E2E_PASSWORD || 'DemoPass1'
const base = process.env.E2E_BASE_URL || 'http://127.0.0.1:5173'

test.describe('Nexus smoke', () => {
  test('login → board → move issue control visible', async ({ page }) => {
    test.setTimeout(120_000)
    await page.goto(`${base}/login`)
    await page.getByLabel(/work email/i).fill(email)
    await page.getByLabel(/^password$/i).fill(password)
    await page.getByRole('button', { name: /^sign in$/i }).click()
    await expect(page).toHaveURL(/\/app\//, { timeout: 60_000 })

    await page.getByRole('link', { name: /Website Redesign|NEX-WEB/i }).first().click()
    await expect(page).toHaveURL(/\/board/, { timeout: 30_000 })
    await expect(page.getByText(/todo|in progress|done/i).first()).toBeVisible({
      timeout: 30_000,
    })
  })
})
