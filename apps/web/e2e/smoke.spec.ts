import { expect, test } from "@playwright/test";

const API_URL = process.env.PLAYWRIGHT_API_URL ?? "http://127.0.0.1:8000";

test.describe("Smoke", () => {
  test("API health responds", async () => {
    const response = await fetch(`${API_URL}/health`);
    expect(response.ok).toBeTruthy();
    const body = (await response.json()) as { status: string; service: string };
    expect(body.status).toBe("ok");
    expect(body.service).toBe("relay-api");
  });

  test("login page renders", async ({ page }) => {
    await page.goto("/login", { waitUntil: "commit" });
    await expect(page.getByTestId("login-page")).toBeVisible();
    await expect(page.getByTestId("login-sign-in")).toBeVisible();
  });
});
