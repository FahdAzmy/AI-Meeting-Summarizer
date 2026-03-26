import { test, expect } from '@playwright/test';

test('History View Load', async ({ page }) => {
  await page.goto('/history');
  
  await expect(page.locator('text=Discussed Q2 planning...')).toBeVisible({ timeout: 2000 });
});
