import { defineConfig, PlaywrightTestConfig } from "@playwright/test"
import { config as baseConfig } from "./playwright.config"
import dotenv from "dotenv"
import path from "path"

dotenv.config({ path: path.resolve(__dirname, ".env") })

const config: PlaywrightTestConfig = {
  ...baseConfig,
  testIgnore: "",
  timeout: 1800_000,
  testMatch: "*regression*",
  expect: {
    toHaveScreenshot: {
      pathTemplate: `./${process.env.SCREENSHOTS_BASE_PATH || "__screenshots__"}/{testFilePath}/{arg}{ext}`,
      maxDiffPixels: 100,
    },
  },
}

export default defineConfig(config)
