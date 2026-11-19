import { defineConfig, devices, PlaywrightTestConfig } from "@playwright/test"
import dotenv from "dotenv"
import path from "path"
import { fileURLToPath } from "url"

/**
 * See https://playwright.dev/docs/test-configuration.
 */

const __dirname = path.dirname(fileURLToPath(import.meta.url))
dotenv.config({ path: path.resolve(__dirname, ".env") })

const PORT = 8888
const BASE_URL = `http://localhost:${PORT}`

// The CI runner has Python and its own Postgres: the server runs directly.
// Locally it runs in the webapp service of docker-compose.yml, against the
// sample database built by `make e2e-prepare`.
const WEB_SERVER_COMMAND = process.env.CI
  ? "uv run python manage.py runserver 0.0.0.0:8888"
  : "docker compose run --rm -p 8888:8888 -e ASSISTANT_V2_STANDALONE_REDIRECT webapp python manage.py runserver 0.0.0.0:8888"
const LOCAL_SAMPLE_DATABASE_URL =
  "postgres://webapp_sample:webapp_sample@webapp-db:5432/webapp_sample" // pragma: allowlist secret

export const config: PlaywrightTestConfig = {
  testDir: "./e2e_tests",
  timeout: 45000,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 1,
  workers: 1,
  reporter: process.env.CI ? "blob" : "html",
  webServer: {
    command: WEB_SERVER_COMMAND,
    port: 8888,
    reuseExistingServer: !process.env.CI,
    env: {
      ...(process.env as Record<string, string>),
      DATABASE_URL:
        process.env.DB_WEBAPP_SAMPLE ??
        process.env.DATABASE_URL ??
        LOCAL_SAMPLE_DATABASE_URL,
      SECRET_KEY: process.env.SECRET_KEY ?? "local-development-only", // pragma: allowlist secret
      BASE_URL: "http://localhost:8888",
      // The debug toolbar is a fixed-position overlay that interferes with
      // layout-sensitive tests (e.g. the autocomplete dropdown clamp at narrow
      // heights). Keep it off for the e2e server regardless of local .env.
      WITH_DJANGO_DEBUG_TOOLBAR: "False",
      // assistant_iframe.spec.ts embeds the assistant from 127.0.0.1, a host
      // distinct from the iframe's.
      ALLOWED_HOSTS: "localhost,127.0.0.1",
      // The tests open the assistant's screens directly, outside any iframe.
      ASSISTANT_V2_STANDALONE_REDIRECT: "False",
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
