import { expect } from "@playwright/test"
import { test } from "./config"

/**
 * Tests for embed script routes
 *
 * These tests verify that all embed script files are accessible
 * and return the correct content type.
 */

test.describe("Embed script routes", () => {
  test("carte.js script is accessible", async ({ page, baseUrl }) => {
    const response = await page.goto(`${baseUrl}/static/carte.js`)
    expect(response?.status()).toBe(200)
    expect(response?.headers()["content-type"]).toMatch(
      /application\/javascript|text\/javascript/,
    )
  })

  test("iframe.js script is accessible", async ({ page, baseUrl }) => {
    const response = await page.goto(`${baseUrl}/static/iframe.js`)
    expect(response?.status()).toBe(200)
    expect(response?.headers()["content-type"]).toMatch(
      /application\/javascript|text\/javascript/,
    )
  })

  test("infotri.js script is accessible", async ({ page, baseUrl }) => {
    const response = await page.goto(`${baseUrl}/infotri/static/infotri.js`)
    expect(response?.status()).toBe(200)
    expect(response?.headers()["content-type"]).toMatch(
      /application\/javascript|text\/javascript/,
    )
  })

  test("infotri-configurator.js script is accessible", async ({ page, baseUrl }) => {
    const response = await page.goto(
      `${baseUrl}/infotri/static/infotri-configurator.js`,
    )
    expect(response?.status()).toBe(200)
    expect(response?.headers()["content-type"]).toMatch(
      /application\/javascript|text\/javascript/,
    )
  })
})
