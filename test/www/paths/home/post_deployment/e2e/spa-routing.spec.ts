import { test, expect } from "../../../../../../src/www/paths/index/node_modules/@playwright/test";

test.describe("SPA routing", () => {
  test.describe("nonexistent routes", () => {
    test("returns 200 for nonexistent page", async ({ page }) => {
      const response = await page.goto("/nonexistent-page-12345");
      const statusIs200 = response?.status() === 200;
      expect(statusIs200).toBe(true);
    });

    test("has content", async ({ page }) => {
      await page.goto("/nonexistent-page-12345");
      const content = await page.content();
      const hasContent = content.length > 0;
      expect(hasContent).toBe(true);
    });
  });

  test.describe("privacy page", () => {
    test("returns 200", async ({ page }) => {
      const response = await page.goto("/privacy.html");
      const statusIs200 = response?.status() === 200;
      expect(statusIs200).toBe(true);
    });

    test("contains privacy content", async ({ page }) => {
      await page.goto("/privacy.html");
      const privacyHeading = page.getByRole("heading", { name: "Privacy Notice", exact: true });
      const isVisible = await privacyHeading.isVisible();
      expect(isVisible).toBe(true);
    });
  });
});

test.describe("home page content", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test.describe("hero section", () => {
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

  test.describe("sections", () => {
    test("has contact section", async ({ page }) => {
      const contactSection = page.locator("#contact");
      const isVisible = await contactSection.isVisible();
      expect(isVisible).toBe(true);
    });

    test("has products section", async ({ page }) => {
      const productsSection = page.locator("#products");
      const isVisible = await productsSection.isVisible();
      expect(isVisible).toBe(true);
    });

    test("has about section", async ({ page }) => {
      const aboutHeading = page.getByRole("heading", { name: "About 10U Labs" });
      const isVisible = await aboutHeading.isVisible();
      expect(isVisible).toBe(true);
    });
  });

  test.describe("product cards", () => {
    test("displays CPUs card", async ({ page }) => {
      const cpusCard = page.getByText("CPUs").first();
      const isVisible = await cpusCard.isVisible();
      expect(isVisible).toBe(true);
    });

    test("displays CPU Sockets card", async ({ page }) => {
      const socketsCard = page.getByText("CPU Sockets").first();
      const isVisible = await socketsCard.isVisible();
      expect(isVisible).toBe(true);
    });

    test("displays Motherboards card", async ({ page }) => {
      const motherboardsCard = page.getByText("Motherboards").first();
      const isVisible = await motherboardsCard.isVisible();
      expect(isVisible).toBe(true);
    });
  });

  test.describe("contact form", () => {
    test("displays send message button", async ({ page }) => {
      const sendButton = page.getByRole("button", { name: "Send Message" });
      const isVisible = await sendButton.isVisible();
      expect(isVisible).toBe(true);
    });
  });

  test.describe("footer", () => {
    test("displays copyright", async ({ page }) => {
      const copyright = page.getByText(/Copyright/);
      const isVisible = await copyright.isVisible();
      expect(isVisible).toBe(true);
    });

    test("displays privacy link", async ({ page }) => {
      const privacyLink = page.getByRole("link", { name: /Privacy/i });
      const isVisible = await privacyLink.isVisible();
      expect(isVisible).toBe(true);
    });
  });
});
