import { defineConfig, devices } from "@playwright/test"
import dotenv from "dotenv"
import path from "path"

/**
 * Read environment variables from file.
 * https://github.com/motdotla/dotenv
 */
// require('dotenv').config();

/**
 * See https://playwright.dev/docs/test-configuration.
 */

dotenv.config({ path: path.resolve(__dirname, ".env") })

const BASE_URL = process.env.BASE_URL

// Extract host and port from BASE_URL for the webServer command
let PLAYWRIGHT_HOST = process.env.PLAYWRIGHT_HOST || "localhost"
let PLAYWRIGHT_PORT = process.env.PLAYWRIGHT_PORT || "8000"

if (BASE_URL) {
  try {
    const url = new URL(BASE_URL)
    PLAYWRIGHT_HOST = url.hostname
    PLAYWRIGHT_PORT = url.port || (url.protocol === "https:" ? "443" : "80")
  } catch (e) {
    // If BASE_URL is invalid, fall back to environment variables or defaults
    console.warn(`Invalid BASE_URL: ${BASE_URL}, using default host and port`)
  }
}

export default defineConfig({
  testDir: "./e2e_tests",
  /* Run tests in files in parallel */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  /* Opt out of parallel tests on CI. */
  workers: process.env.CI ? 1 : undefined,
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: "html",
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    baseURL: BASE_URL,
    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: "on-first-retry",
  },

  /* Run local dev server before starting the tests */
  webServer: {
    // skip-checks and noreload ensures django runserver starts faster
    command: `uv run python manage.py runserver ${process.env.DEBUG?.toLowerCase() === "true" ? "--noreload --skip-checks" : ""} ${PLAYWRIGHT_HOST}:${PLAYWRIGHT_PORT}`,
    url: process.env.BASE_URL,
    reuseExistingServer: !process.env.CI,
    timeout: 10000,
    env: process.env,
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: "chromium",
      grepInvert: /@mobile/,
      use: {
        ...devices["Desktop Chrome"],
        userAgent: "playwright",
        launchOptions: {
          args: ["--ignore-certificate-errors"],
        },
      },
    },
    {
      name: "Mobile Safari",
      grepInvert: /@desktop/,
      grep: /@mobile|@responsive/,
      use: {
        ...devices["iPhone 12"],
        userAgent: "playwright",
      },
    },
  ],
})
