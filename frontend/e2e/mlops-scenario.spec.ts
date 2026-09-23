import { test, expect } from '@playwright/test';

test.describe('MLOps Platform E2E Scenario', () => {
  test('Complete Model Lifecycle', async ({ page }) => {
    // 1. Visit Models page
    await page.goto('/');
    await expect(page).toHaveTitle(/Frontend/); // from index.html

    // Open Create Model dialog (assuming the button exists. Actually, looking at models-list.ts, there is no "Create Model" button! The assignment seeded it or requires API. Wait, I should check models-list.ts.)
    // Let's create the model via API directly for the setup, or if there is a UI button, click it.
    // If the UI doesn't have a Create Model button, we will just use an existing seeded model like 'pump-failure-prediction-xgboost'
    
    // We will navigate to the model detail page for the seeded model
    // We will navigate to the model detail page for the seeded model
    const modelRow = page.locator('tr', { hasText: 'Pump Failure Predictor' });
    await modelRow.locator('button:has-text("View Details")').click();
    await expect(page).toHaveURL(/\/models\/pump-failure-predictor/);

    // 2. Register version
    const versionStr = `2.0.0-e2e-${Date.now()}`;
    await page.click('button:has-text("New Version")');
    await page.fill('input[name="version"]', versionStr);
    await page.click('mat-select[name="stage"]');
    await page.click('mat-option:has-text("DRAFT")');
    await page.fill('input[name="artifact_uri"]', 's3://bucket/e2e/model.pkl');
    await page.click('button:has-text("Create")');
    
    // Wait for the version to appear
    await expect(page.locator('table')).toContainText(versionStr);

    // 3. Approve version
    // The approve button should be in the row for our new version
    const row = page.locator('tr', { hasText: versionStr });
    await row.locator('button:has-text("Approve")').click();
    
    // Wait for success toast
    await expect(page.getByText('Version approved successfully!')).toBeVisible();
    
    // The text should change from DRAFT to APPROVED
    await expect(row).toContainText('APPROVED');

    // 4. Deploy
    await row.locator('button:has-text("Deploy")').click();
    await page.click('mat-select[name="environment"]');
    await page.click('mat-option:has-text("Production")');
    await page.locator('mat-dialog-actions button:has-text("Deploy")').click();
    
    // Wait for success toast and redirect
    await expect(page.getByText('Deployment requested successfully!')).toBeVisible();
    await expect(page).toHaveURL(/\/deployments/);

    // 5. View metrics
    await page.goto('/models/pump-failure-predictor');
    await page.click('div.mat-mdc-tab-labels div:has-text("Monitoring Metrics")');
    // Ensure metrics table is visible
    await expect(page.locator('table').nth(1)).toBeVisible();

    // 6. Roll back (Need to navigate to deployments and click rollback on the succeeded deployment)
    await page.goto('/deployments');
    const deployRow = page.locator('tr', { hasText: 'SUCCEEDED' }).first();
    
    // Poll until deployment succeeds (since it takes a few seconds in the background)
    await expect(async () => {
      await page.click('button:has-text("Refresh")');
      await expect(deployRow).toBeVisible({ timeout: 1000 });
    }).toPass({ timeout: 30000, intervals: [2000] });

    await deployRow.locator('button[title="Rollback"]').click();
    
    // Check that a new REQUESTED deployment appears
    await expect(page.locator('tr', { hasText: 'REQUESTED' }).first()).toBeVisible({ timeout: 5000 });
  });
});
