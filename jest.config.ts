import type { Config } from "jest"

const config: Config = {
    preset: "ts-jest",
    testEnvironment: "jsdom",
    testEnvironmentOptions: {
        html: '<html lang="zh-cmn-Hant"></html>',
        url: "https://jestjs.io/",
        userAgent: "Agent/007",
    },
    transform: {
        "^.+\\.ts?$": "ts-jest",
    },
    transformIgnorePatterns: ["/node_modules/(?!crypto-random-string)(.*)"],
}

export default config
