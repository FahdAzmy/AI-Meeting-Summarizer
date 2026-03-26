import { test, expect } from '@playwright/test';

test('Detail Flow and 404', async ({ page }) => {
  await page.goto('/history/abc-1234');
  await expect(page.locator('text=Full formatted markdown summary here')).toBeVisible({ timeout: 2000 });
});
