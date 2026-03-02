import { defineConfig, devices, PlaywrightTestConfig } from "@playwright/test"
import dotenv from "dotenv"
import path from "path"

/**
 * See https://playwright.dev/docs/test-configuration.
 */

dotenv.config({ path: path.resolve(__dirname, ".env") })

const PORT = 8888
const BASE_URL = `http://localhost:${PORT}`

export const config: PlaywrightTestConfig = {
  testDir: "./e2e_tests",
  timeout: 45000,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 4,
  workers: 1,
  reporter: "html",
  webServer: {
    command: `uv run python manage.py runserver 0.0.0.0:${PORT}`,
    port: PORT,
    reuseExistingServer: !process.env.CI,
    env: {
      ...(process.env as Record<string, string>),
      DATABASE_URL: (process.env.SAMPLE_DATABASE_URL ?? process.env.DATABASE_URL)!,
      SECRET_KEY: process.env.SECRET_KEY!,
      BASE_URL: BASE_URL,
    },
    cwd: path.resolve(__dirname),
  },
  use: {
    baseURL: BASE_URL,
    trace: "on-first-retry",
  },
  expect: {
    toHaveScreenshot: {
      pathTemplate: `./__screenshots__/{testFilePath}/{testName}/{arg}{ext}`,
      maxDiffPixelRatio: 0.01,
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
            "--use-angle=gl",
            "--use-gl=angle",
            "--ignore-gpu-blacklist",
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
