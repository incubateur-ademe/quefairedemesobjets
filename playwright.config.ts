import { defineConfig, devices } from "@playwright/test"
import dotenv from 'dotenv';
import path from 'path'

/**
 * Read environment variables from file.
 * https://github.com/motdotla/dotenv
 */
// require('dotenv').config();

/**
 * See https://playwright.dev/docs/test-configuration.
 */

dotenv.config({ path: path.resolve(__dirname, '.env') });

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
    baseURL: process.env.LVAO_BASE_URL!,
    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: "on-first-retry",
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: "chromium",
      grepInvert: /Mobile/,
      use: {
        ...devices["Desktop Chrome"],
        launchOptions: {
          args: ['--ignore-certificate-errors']
        }
      },

    },
    {
      name: "Mobile Safari",
      grepInvert: /Desktop/,
      use: {
        ...devices["iPhone 12"],
      },
    },
  ],

  /* Run your local dev server before starting the tests */
  // webServer: {
  //     command: "honcho start -f Procfile.dev",
  //     url: "http://localhost:8000",
  //     reuseExistingServer: !process.env.CI,
  // },
})
