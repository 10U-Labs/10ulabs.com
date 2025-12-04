import { test, expect } from "@playwright/test";

test.describe("404 Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/this-page-does-not-exist-12345");
  });

  test.describe("error display", () => {
    test("displays 404 heading", async ({ page }) => {
      const heading = page.getByRole("heading", { name: "404" });
      const isVisible = await heading.isVisible();
      expect(isVisible).toBe(true);
    });

    test("displays error message", async ({ page }) => {
      const message = page.getByText("Oops! Page not found");
      const isVisible = await message.isVisible();
      expect(isVisible).toBe(true);
    });
  });

  test.describe("navigation", () => {
    test("displays return home link", async ({ page }) => {
      const link = page.getByRole("link", { name: "Return to Home" });
      const isVisible = await link.isVisible();
      expect(isVisible).toBe(true);
    });

    test("return home link navigates to home page", async ({ page }) => {
      await page.getByRole("link", { name: "Return to Home" }).click();
      await page.waitForURL("/");
      const isHome = page.url().endsWith("/");
      expect(isHome).toBe(true);
    });
  });
});
