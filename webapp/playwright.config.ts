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
  webServer: {
    command: "uv run python manage.py runserver 0.0.0.0:8888",
    port: 8888,
    reuseExistingServer: !process.env.CI,
    env: {
      ...(process.env as Record<string, string>),
      DATABASE_URL: (process.env.SAMPLE_DATABASE_URL ?? process.env.DATABASE_URL)!,
      SECRET_KEY: process.env.SECRET_KEY!,
      BASE_URL: "http://localhost:8888",
    },
    cwd: path.resolve(__dirname),
  },
  use: {
    baseURL: "http://localhost:8888",
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
            // "--use-gl=swiftshader",
            // "--disable-gpu-sandbox",
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
