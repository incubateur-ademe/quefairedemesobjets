import type { Config } from "jest"

const config: Config = {
  testEnvironment: "jsdom",
  roots: ["<rootDir>/src"],
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
  transform: {
    "^.+\\.tsx?$": [
      "ts-jest",
      {
        tsconfig: {
          jsx: "react-jsx",
          module: "commonjs",
          moduleResolution: "node10",
          esModuleInterop: true,
          isolatedModules: true,
          // CommonJS output for jest (Parcel builds the real bundle)
          ignoreDeprecations: "6.0",
        },
      },
    ],
  },
  moduleNameMapper: {
    // Parcel named pipelines (ex: data-url:remixicon/icons/…svg)
    "^data-url:.*$": "<rootDir>/src/__mocks__/dataUrl.ts",
    "\\.css$": "<rootDir>/src/__mocks__/style.ts",
  },
}

export default config
