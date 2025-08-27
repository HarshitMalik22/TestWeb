
import { test } from '@playwright/test';
import { expect } from '@playwright/test';

test('GeneratedTest_2025-08-25', async ({ page, context }) => {
  
    // Navigate to URL
    await page.goto('https://www.hardees.com/');

    // Click element
    await page.click('text=Join My Rewards');

    // Click element
    await page.click('text=View Full Menu');
});