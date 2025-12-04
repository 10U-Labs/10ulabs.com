import { test, expect } from "@playwright/test";

test.describe("Home Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test.describe("page load", () => {
    test("loads successfully", async ({ page }) => {
      const statusOk = page.url().includes("10ulabs.com");
      expect(statusOk).toBe(true);
    });

    test("displays company name", async ({ page }) => {
      const companyName = page.getByRole("heading", { name: "10U Labs, LLC" });
      const isVisible = await companyName.isVisible();
      expect(isVisible).toBe(true);
    });

    test("displays tagline", async ({ page }) => {
      const tagline = page.getByText("Building flexible computing hardware");
      const isVisible = await tagline.isVisible();
      expect(isVisible).toBe(true);
    });
  });

  test.describe("navigation buttons", () => {
    test("get in touch button is visible", async ({ page }) => {
      const button = page.getByRole("button", { name: "Get in Touch" });
      const isVisible = await button.isVisible();
      expect(isVisible).toBe(true);
    });

    test("our products button is visible", async ({ page }) => {
      const button = page.getByRole("button", { name: "Our Products" });
      const isVisible = await button.isVisible();
      expect(isVisible).toBe(true);
    });

    test("get in touch button scrolls to contact section", async ({ page }) => {
      await page.getByRole("button", { name: "Get in Touch" }).click();
      const contactSection = page.locator("#contact");
      const boundingBox = await contactSection.boundingBox();
      const isInViewport = boundingBox !== null && boundingBox.y >= 0 && boundingBox.y < 768;
      expect(isInViewport).toBe(true);
    });

    test("our products button scrolls to products section", async ({ page }) => {
      await page.getByRole("button", { name: "Our Products" }).click();
      const productsSection = page.locator("#products");
      const boundingBox = await productsSection.boundingBox();
      const isInViewport = boundingBox !== null && boundingBox.y >= 0 && boundingBox.y < 768;
      expect(isInViewport).toBe(true);
    });
  });

  test.describe("products section", () => {
    test("displays CPUs card", async ({ page }) => {
      const card = page.getByRole("heading", { name: "CPUs" });
      const isVisible = await card.isVisible();
      expect(isVisible).toBe(true);
    });

    test("displays CPU Sockets card", async ({ page }) => {
      const card = page.getByRole("heading", { name: "CPU Sockets" });
      const isVisible = await card.isVisible();
      expect(isVisible).toBe(true);
    });

    test("displays Motherboards card", async ({ page }) => {
      const card = page.getByRole("heading", { name: "Motherboards" });
      const isVisible = await card.isVisible();
      expect(isVisible).toBe(true);
    });
  });

  test.describe("contact form", () => {
    test("displays name input", async ({ page }) => {
      const input = page.getByPlaceholder("Name *");
      const isVisible = await input.isVisible();
      expect(isVisible).toBe(true);
    });

    test("displays email input", async ({ page }) => {
      const input = page.getByPlaceholder("Email *");
      const isVisible = await input.isVisible();
      expect(isVisible).toBe(true);
    });

    test("displays message textarea", async ({ page }) => {
      const textarea = page.getByPlaceholder("Message *");
      const isVisible = await textarea.isVisible();
      expect(isVisible).toBe(true);
    });

    test("displays submit button", async ({ page }) => {
      const button = page.getByRole("button", { name: "Send Message" });
      const isVisible = await button.isVisible();
      expect(isVisible).toBe(true);
    });

    test("accepts text input in name field", async ({ page }) => {
      const input = page.getByPlaceholder("Name *");
      await input.fill("Test User");
      const value = await input.inputValue();
      expect(value === "Test User").toBe(true);
    });

    test("accepts text input in email field", async ({ page }) => {
      const input = page.getByPlaceholder("Email *");
      await input.fill("test@example.com");
      const value = await input.inputValue();
      expect(value === "test@example.com").toBe(true);
    });

    test("accepts text input in message field", async ({ page }) => {
      const textarea = page.getByPlaceholder("Message *");
      await textarea.fill("This is a test message");
      const value = await textarea.inputValue();
      expect(value === "This is a test message").toBe(true);
    });
  });

  test.describe("footer", () => {
    test("displays copyright notice", async ({ page }) => {
      const copyright = page.getByText("Copyright © 2025 10U Labs, LLC");
      const isVisible = await copyright.isVisible();
      expect(isVisible).toBe(true);
    });

    test("displays privacy notice link", async ({ page }) => {
      const link = page.getByRole("link", { name: "Privacy Notice" });
      const isVisible = await link.isVisible();
      expect(isVisible).toBe(true);
    });

    test("privacy notice link has correct href", async ({ page }) => {
      const link = page.getByRole("link", { name: "Privacy Notice" });
      const href = await link.getAttribute("href");
      expect(href === "/privacy.html").toBe(true);
    });
  });
});
