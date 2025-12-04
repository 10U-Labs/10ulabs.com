import { defineConfig } from "@playwright/test";

export default defineConfig({
  forbidOnly: !!process.env.CI,
  fullyParallel: true,
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
  ],
  reporter: "html",
  retries: process.env.CI ? 2 : 0,
  testDir: "./",
  use: {
    baseURL: process.env.BASE_URL || "https://10ulabs.com",
    trace: "on-first-retry",
  },
  workers: process.env.CI ? 1 : undefined,
});
