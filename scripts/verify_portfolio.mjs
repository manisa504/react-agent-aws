/** Browser acceptance for the public portfolio and its backend-free playground. */
import {
  chromium,
  expect,
} from "../frontend/node_modules/@playwright/test/index.mjs";
import { mkdir } from "node:fs/promises";
const base = (process.env.PORTFOLIO_URL || "http://127.0.0.1:8080/").replace(
  /\/?$/,
  "/",
);
const browser = await chromium.launch({
  headless: true,
  ...(process.env.CHROME_PATH
    ? { executablePath: process.env.CHROME_PATH }
    : {}),
});
const errors = [];
try {
  await mkdir(".build", { recursive: true });
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1050 },
  });
  page.on("pageerror", (error) => errors.push(error.message));
  page.setDefaultTimeout(15000);
  console.log("Checking portfolio at", base);
  const failed = [];
  page.on("response", (response) => {
    if (response.status() >= 400)
      failed.push(`${response.status()} ${response.url()}`);
  });
  await page.goto(base, { waitUntil: "networkidle", timeout: 20000 });
  console.log("Portfolio loaded");
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "An agent you",
  );
  await page
    .locator("img")
    .evaluateAll((images) =>
      images.forEach((image) => (image.loading = "eager")),
    );
  await page.waitForFunction(
    () =>
      [...document.images].every(
        (image) => image.complete && image.naturalWidth > 0,
      ),
    {},
    { timeout: 15000 },
  );
  console.log("Images loaded");
  await expect(page.locator(".atlas-card")).toHaveCount(9);
  await page
    .getByRole("button", { name: "Runtime & security", exact: true })
    .click();
  await expect(page.locator(".atlas-card:not([hidden])")).toHaveCount(5);
  await page
    .getByRole("button", { name: "Data & operations", exact: true })
    .click();
  await expect(page.locator(".atlas-card:not([hidden])")).toHaveCount(4);
  await page.getByRole("button", { name: "All nine", exact: true }).click();
  await page.getByRole("button", { name: "Explore diagram" }).first().click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await page.getByRole("tab", { name: "02 Calculate safely" }).click();
  await expect(page.locator("#trace-output")).toHaveText("15 * 60 * 8 = 7200");
  await page.getByRole("tab", { name: "02 Calculate safely" }).focus();
  await page.keyboard.press("End");
  await expect(
    page.getByRole("tab", { name: "03 Validate completion" }),
  ).toHaveAttribute("aria-selected", "true");
  await expect(page.locator("#trace-output")).toContainText(
    "3,239 input / 384 output",
  );
  await page.locator(".evaluation-details summary").first().click();
  await expect(page.locator(".evaluation-details tbody tr")).toHaveCount(12);
  await page.locator(".evaluation-details summary").first().click();
  await expect(page.locator(".result-card table tbody tr")).toHaveCount(2);
  await page.locator(".gallery-button").first().click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page.locator("#dialog-image")).toHaveAttribute(
    "data-kind",
    "screenshot",
  );
  await page.keyboard.press("Escape");
  await page.screenshot({
    path: ".build/portfolio-desktop.png",
    fullPage: true,
    animations: "disabled",
  });
  await page.setViewportSize({ width: 320, height: 900 });
  if (
    await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)
  )
    throw Error("Portfolio overflows at 320px");
  await page.screenshot({
    path: ".build/portfolio-mobile.png",
    fullPage: true,
    animations: "disabled",
  });
  await page
    .getByRole("link", { name: "Explore the interactive demo" })
    .click();
  await expect(page.getByText("MOCK · STATIC DEMO")).toBeVisible();
  // After initial static assets load, all scenarios must run with network blocked.
  await page.waitForLoadState("networkidle");
  const runtimeRequests = [];
  await page.route("**/*", (route) => {
    runtimeRequests.push(route.request().url());
    return route.abort();
  });
  await page.getByLabel("Playback", { exact: true }).selectOption("fast");
  const cases = [
    ["AWS decision", "Succeeded", "FINAL_ANSWER", 3],
    ["Calculation", "Succeeded", "FINAL_ANSWER", 2],
    ["Unsupported", "Failed", "UNSUPPORTED", 2],
    ["Bounded loop", "Limit reached", "STEP_LIMIT", 5],
    ["Invalid tool", "Failed", "INVALID_TOOL", 1],
    ["Service failure", "Failed", "MODEL_ERROR", 1],
  ];
  for (const [name, status, reason, steps] of cases) {
    await page.getByRole("button", { name, exact: true }).click();
    await page
      .getByRole("button", { name: "Run scenario", exact: false })
      .click();
    await expect(page.getByRole("status")).toHaveText(status);
    await expect(page.locator("#termination")).toHaveText(reason);
    await expect(page.locator("#events > li")).toHaveCount(steps);
    if (name === "AWS decision") {
      await expect(page.locator("#answer")).toContainText("7,200");
      await expect(page.locator("#sources details")).toHaveCount(2);
      await page.locator("#events summary").first().click();
      await expect(page.locator("#events pre").first()).toContainText(
        "SQS EventBridge",
      );
    }
    if (
      await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth,
      )
    )
      throw Error(`${name} overflows at 320px`);
    console.log("PASS static scenario:", name, status, reason, steps);
  }
  for (const limit of ["3", "8"]) {
    await page
      .getByRole("button", { name: "Bounded loop", exact: true })
      .click();
    await page.getByLabel("Step limit", { exact: true }).selectOption(limit);
    await page
      .getByRole("button", { name: "Run scenario", exact: false })
      .click();
    await expect(page.getByRole("status")).toHaveText("Limit reached");
    await expect(page.locator("#events > li")).toHaveCount(Number(limit));
  }
  await page.getByRole("button", { name: "Calculation", exact: true }).click();
  await page.getByLabel("Minutes", { exact: true }).fill("2");
  await page.getByLabel("Images per second", { exact: true }).fill("3");
  await page
    .getByRole("button", { name: "Run scenario", exact: false })
    .click();
  await expect(page.getByRole("status")).toHaveText("Succeeded");
  await expect(page.locator("#answer")).toContainText("360 images");
  await page.getByRole("button", { name: "AWS decision", exact: true }).click();
  await page.getByRole("button", { name: "Calculation", exact: true }).click();
  await expect(page.getByLabel("Planning task")).toHaveValue(
    "Calculate how many images arrive in 2 minutes at 3 images per second.",
  );
  await page.getByLabel("Minutes", { exact: true }).fill("0");
  await page
    .getByRole("button", { name: "Run scenario", exact: false })
    .click();
  await expect(page.getByRole("alert")).toContainText("between 1 and 10,000");
  await expect(page.locator("#events > li")).toHaveCount(0);
  await page.getByRole("button", { name: "AWS decision", exact: true }).click();
  await page.getByLabel("Planning task").fill('<img src=x onerror="alert(1)">');
  await expect(page.locator('img[src="x"]')).toHaveCount(0);
  await page.getByLabel("Planning task").fill("");
  await expect(
    page.getByRole("button", { name: "Run scenario", exact: false }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Bounded loop", exact: true }).click();
  await page.getByLabel("Playback", { exact: true }).selectOption("normal");
  await page
    .getByRole("button", { name: "Run scenario", exact: false })
    .click();
  await expect(page.getByRole("status")).toHaveText("Queued");
  await expect(page.getByRole("status")).toHaveText("Running");
  await page.getByRole("button", { name: "Stop & reset", exact: true }).click();
  await page.waitForTimeout(850);
  await expect(page.getByRole("status")).toHaveText("Ready");
  await expect(page.locator("#events > li")).toHaveCount(0);
  await page.getByRole("button", { name: "AWS decision", exact: true }).click();
  await page.getByLabel("Playback", { exact: true }).selectOption("fast");
  await page
    .getByRole("button", { name: "Run scenario", exact: false })
    .click();
  await expect(page.getByRole("status")).toHaveText("Succeeded");
  await page.screenshot({
    path: ".build/static-demo-mobile.png",
    fullPage: true,
    animations: "disabled",
  });
  await page.setViewportSize({ width: 1440, height: 1100 });
  await page.screenshot({
    path: ".build/static-demo-desktop.png",
    fullPage: true,
    animations: "disabled",
  });
  if (runtimeRequests.length || errors.length || failed.length)
    throw Error(JSON.stringify({ runtimeRequests, errors, failed }));
  console.log(
    "PASS portfolio assets, diagram dialog, mobile layout, scenario budgets, arithmetic validation, queued/running states, reset cancellation and zero runtime network requests",
  );
} finally {
  await browser.close();
}
