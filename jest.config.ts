import type { Config } from "jest"

const config: Config = {
  preset: "ts-jest",
  testEnvironment: "jsdom",
  verbose: false,
  transform: {
    "^.+\\.ts?$": "ts-jest",
  },
}

export default config
