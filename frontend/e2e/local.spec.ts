import { test, expect } from "@playwright/test";
test("local two-tool workflow, citations and screenshot", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "A little more evidence",
  );
  await page.getByRole("link", { name: "Open the workbench" }).click();
  await expect(page.getByText("MOCK · LOCAL DEMO")).toBeVisible();
  await expect(page.getByRole("button", { name: "Run task" })).toBeDisabled();
  await page.getByRole("button", { name: "AWS decision" }).click();
  await page.getByRole("button", { name: "Run task" }).click();
  await expect(page.getByRole("status")).toHaveText("Succeeded");
  await expect(
    page.getByText(/Calculation: 15 \* 60 \* 8 = 7200/),
  ).toBeVisible();
  await expect(page.getByRole("listitem")).toHaveCount(3);
  await page.getByText("View tool observation").first().click();
  await expect(page.locator("pre").first()).toContainText("AWS-SQS");
  await page.getByText("View tool observation").first().click();
  await expect(page.getByText("Not reported")).toBeVisible();
  await page.setViewportSize({ width: 1440, height: 1100 });
  await page.screenshot({
    path: "../docs/assets/workbench-local.png",
    fullPage: true,
    animations: "disabled",
  });
  await page.reload();
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "Plan with tools.",
  );
  expect(errors).toEqual([]);
});
test("loop, failure, unsupported and mobile layout", async ({ page }) => {
  await page.goto("/app");
  await page.getByRole("button", { name: "Bounded loop" }).click();
  await page.getByRole("button", { name: "Run task" }).click();
  await expect(page.getByRole("status")).toHaveText("Step limit reached");
  await expect(page.getByText("5 / 5")).toBeVisible();
  await page.getByRole("button", { name: "Unsupported", exact: true }).click();
  await page.getByRole("button", { name: "Run task" }).click();
  await expect(page.getByRole("status")).toHaveText("Failed");
  await expect(
    page.getByText(/Evidence insufficient · this answer is unsupported/),
  ).toBeVisible();
  await page.getByLabel("Planning task").fill("[invalid]");
  await page.getByRole("button", { name: "Run task" }).click();
  await expect(
    page.getByText("The requested tool is not allowed."),
  ).toBeVisible();
  await page.setViewportSize({ width: 320, height: 900 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "../docs/assets/workbench-mobile.png",
    fullPage: true,
    animations: "disabled",
  });
});
