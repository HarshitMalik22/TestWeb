
import { test } from '@playwright/test';
import { expect } from '@playwright/test';

test('Hardees_Test_2025-08-25', async ({ page, context }) => {
  
    // Click element
    await page.click('text=Menu');

    // Click element
    await page.click('text=Order');

    // Click element
    await page.click('text=Menu');

    // Click element
    await page.click('text=Promotions');

    // Click element
    await page.click('text=Store Locator');

    // Click element
    await page.click('text=Order');

    // Click element
    await page.click('text=Promotions');

    // Click element
    await page.click('text=Store Locator');
});