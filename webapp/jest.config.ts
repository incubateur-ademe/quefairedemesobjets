import type { Config } from "jest"

const config: Config = {
  preset: "ts-jest",
  testEnvironment: "jsdom",
  verbose: false,
  setupFiles: ["dotenv/config"],
  transform: {
    "^.+\\.ts?$": "ts-jest",
  },
}

export default config
