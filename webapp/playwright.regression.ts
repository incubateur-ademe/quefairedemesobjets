import { defineConfig, PlaywrightTestConfig } from "@playwright/test"
import { config as baseConfig } from "./playwright.config"
import dotenv from "dotenv"
import path from "path"

dotenv.config({ path: path.resolve(__dirname, ".env") })

const config: PlaywrightTestConfig = {
  ...baseConfig,
  testIgnore: "",
  testMatch: "*regression*",
}

export default defineConfig(config)
