import { test as base } from "@playwright/test"
import dotenv from "dotenv"
import path from "path"

export type TestOptions = {
  baseUrl: string
}
dotenv.config({ path: path.resolve(__dirname, ".env") })

export const test = base.extend<TestOptions>({
  // Define an option and provide a default value.
  // We can later override it in the config.
  baseUrl: [process.env.BASE_URL!, { option: true }],
})
