import { test, expect } from '@playwright/test';

test('Dashboard Join Meeting Flow', async ({ page }) => {
  await page.goto('/');
  
  await page.fill('input[name="meeting_link"]', 'https://meet.google.com/abc-defg-hij');
  await page.fill('input[name="emails"]', 'user@example.com');
  
  await page.click('button[type="submit"]');
  
  // Wait for polling UI to show up
  await expect(page.locator('text=Generating the LLM analytical summary')).toBeVisible({ timeout: 10000 });
});
