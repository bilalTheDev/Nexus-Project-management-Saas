/**
 * Phase 1 acceptance smoke stubs.
 * Run once Playwright is installed: npx playwright test
 *
 * Full acceptance (workspace → Scrum project → epic/stories → sprint →
 * conflict → tour) requires a seeded backend and will be expanded in CI.
 */
import { test, expect } from '@playwright/test'

test.describe('Phase 1 smoke', () => {
  test('landing loads without Atlassian branding', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText(/Nexus/i).first()).toBeVisible()
    await expect(page.locator('body')).not.toContainText('Jira Software')
  })
})
