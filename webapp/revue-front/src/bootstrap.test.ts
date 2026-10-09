import { readBootstrap } from "./bootstrap"

describe("readBootstrap", () => {
  it("reads the JSON rendered by Django", () => {
    document.body.innerHTML = `<script id="revue-bootstrap" type="application/json">
      {"basepath": "/data/revue/", "apiBase": "/api/suggestions", "adminBase": "/admin/",
       "environment": "test", "user": {"id": 1, "username": "admin"}}</script>`

    expect(readBootstrap().user.username).toBe("admin")
  })

  it("fails loudly when the page has no bootstrap", () => {
    document.body.innerHTML = ""

    expect(() => readBootstrap()).toThrow("Missing #revue-bootstrap")
  })
})
