import { expect, test } from "@playwright/test";

test("learner assessment flow runs with 1.5x UI motion and shows tiered badge", async ({ page }) => {
  await page.goto("/?testSpeed=1.5");

  await expect(page.getByRole("heading", { name: "Intern workspace" })).toBeVisible();
  await expect(page.locator(".pipeline-stage-rail").getByText("Profile", { exact: true })).toBeVisible();
  await expect(page.locator(".pipeline-stage-rail").getByText("Badge", { exact: true })).toBeVisible();

  const speedMode = await page.evaluate(() => document.documentElement.dataset.testSpeed);
  expect(speedMode).toBe("1.5");

  await page
    .getByRole("button", { name: "Execute the full learner pipeline for the selected persona and current week count" })
    .click();

  await expect(page.getByRole("heading", { name: "Final assessment" })).toBeVisible({ timeout: 60_000 });
  await expect(page.getByRole("heading", { name: "Workload-aware study plan" })).toBeVisible();

  await page
    .getByRole("button", { name: "Fill the assessment with correct demo answers to preview the passing path" })
    .click();
  await page
    .getByRole("button", {
      name: "Submit selected answers and calculate readiness, booking guidance, and badge eligibility"
    })
    .click();

  await expect(page.getByText("Perfect Score!")).toBeVisible({ timeout: 60_000 });
  await expect(page.getByText("Status: 100% Mastery")).toBeVisible();

  await page.getByRole("button", { name: "Open the manager portal for team readiness, risks, and buddy matching" }).click();
  await expect(page.getByRole("heading", { name: "Program manager portal" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Avery Stone readiness PDF" })).toBeVisible();
  await expect(page.locator(".embedded-reports")).toContainText("L-1001_AZ-204_readiness.pdf");
});
