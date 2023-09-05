import type { Config } from "jest"

const config: Config = {
    preset: "ts-jest/presets/default-esm",
    testEnvironment: "jsdom",
    testEnvironmentOptions: {
        html: '<html lang="zh-cmn-Hant"></html>',
        url: "https://jestjs.io/",
        userAgent: "Agent/007",
    },
    verbose: true,
}

export default config
