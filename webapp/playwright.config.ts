import { defineConfig, devices, PlaywrightTestConfig } from "@playwright/test"
import dotenv from "dotenv"
import path from "path"

/**
 * See https://playwright.dev/docs/test-configuration.
 */

dotenv.config({ path: path.resolve(__dirname, ".env") })

export const config: PlaywrightTestConfig = {
  testDir: "./e2e_tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 4,
  workers: 1,
  reporter: "html",
  use: {
    baseURL: process.env.BASE_URL!,
    trace: "on-first-retry",
  },
  expect: {
    toHaveScreenshot: {
      pathTemplate: `./__screenshots__/{testFilePath}/{testName}/{arg}{ext}`,
      maxDiffPixels: 100,
    },
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
          args: [
            "--ignore-certificate-errors",
            "--use-gl=swiftshader",
            "--disable-gpu-sandbox",
          ],
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
}

export default defineConfig(config)
