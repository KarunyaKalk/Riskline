import { test, expect } from '@playwright/test';

test.describe('DevOps Risk Platform Full User Journey E2E Flow', () => {
  test('User Signup -> Submit Deployment Change -> View Risk Assessment -> Post Note', async ({ page }) => {
    // 1. Visit signup page
    await page.goto('/signup');
    await expect(page).toHaveTitle(/DevOps Risk/i);

    // 2. Fill organization signup
    await page.fill('input[placeholder="Acme Engineering"]', 'E2E Test Corp');
    await page.fill('input[placeholder="admin@acme.com"]', `e2e_user_${Date.now()}@test.com`);
    await page.fill('input[placeholder="Min 8 chars"]', 'SecurePassword123!');
    await page.click('button:has-text("Provision Organization")');

    // 3. Verify Dashboard Mission Control loads
    await expect(page.locator('text=DevOps Risk Overview')).toBeVisible({ timeout: 10000 });

    // 4. Navigate to Changes & Submit new deployment change
    await page.click('button:has-text("Changes & Risk")');
    await page.click('button:has-text("+ Submit New Change")');
    await page.fill('input[placeholder*="Upgrade Postgres"]', 'E2E Security Auth Token Rotation');
    await page.fill('textarea[placeholder*="Provide migration"]', 'Updating JWT signing key secrets and rotating encryption keys.');
    await page.click('button:has-text("Submit Change for Risk Analysis")');

    // 5. Verify change appears in list and click View Risk Breakdown
    await expect(page.locator('text=E2E Security Auth Token Rotation')).toBeVisible({ timeout: 10000 });
    await page.click('button:has-text("View Risk Breakdown")');

    // 6. Verify Technical and Business Risk Summaries appear
    await expect(page.locator('text=Technical Summary')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Business Summary')).toBeVisible();

    // 7. Navigate to Notes & Post a Note
    await page.click('button:has-text("Notes & Ideas")');
    await page.click('button:has-text("+ Post New Note")');
    await page.fill('input[placeholder*="Postgres DB Migration"]', 'E2E Test Decision Note');
    await page.fill('textarea[placeholder*="Describe context"]', 'We decided to proceed with rolling security key rotation.');
    await page.click('button:has-text("Post Note")');

    // 8. Verify note appears live on board
    await expect(page.locator('text=E2E Test Decision Note')).toBeVisible({ timeout: 5000 });
  });
});
