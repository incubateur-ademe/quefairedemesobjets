import { defineConfig } from "@playwright/test"
import dotenv from "dotenv"
import path from "path"

dotenv.config({ path: path.resolve(__dirname, ".env") })

/**
 * Playwright config for Chrome Extension e2e tests.
 *
 * These tests use a custom fixture with chromium.launchPersistentContext
 * to load the extension, so they don't use the standard projects config.
 * They must run headed (extensions don't work in headless mode).
 *
 * Usage: npm run e2e_test:extension
 */
export default defineConfig({
  testDir: "./e2e_tests",
  testMatch: "chrome_extension.spec.ts",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 2,
  workers: 1,
  reporter: "html",
  use: {
    trace: "on-first-retry",
  },
})
