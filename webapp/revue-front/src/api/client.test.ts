/**
 * @jest-environment node
 */
import createClient from "openapi-fetch"

import { ApiError, createCsrfMiddleware, readCookie, unwrap } from "./client"

describe("readCookie", () => {
  it("reads a cookie among others", () => {
    expect(readCookie("csrftoken", "a=1; csrftoken=abc; b=2")).toBe("abc")
    expect(readCookie("csrftoken", "a=1")).toBeUndefined()
  })
})

describe("csrfMiddleware", () => {
  type Method = "get" | "post" | "put" | "patch" | "delete"

  const run = async (method: Method) => {
    let sent: Request | undefined
    const client = createClient<{ "/test": Record<Method, object> }>({
      baseUrl: "http://localhost",
      fetch: async (input) => {
        sent = input as Request
        return new Response("{}")
      },
    })
    client.use(createCsrfMiddleware(() => "a=1; csrftoken=token123"))
    await client.request(method, "/test")
    return sent!
  }

  it.each<Method>(["post", "put", "patch", "delete"])(
    "sets the token on %s",
    async (method) => {
      expect((await run(method)).headers.get("X-CSRFToken")).toBe("token123")
    },
  )

  it("does not set the token on GET", async () => {
    expect((await run("get")).headers.get("X-CSRFToken")).toBeNull()
  })
})

describe("unwrap", () => {
  it("returns the data of a successful response", async () => {
    const response = new Response(null, { status: 200 })
    await expect(
      unwrap(Promise.resolve({ data: { id: 1 }, response })),
    ).resolves.toEqual({ id: 1 })
  })

  it("throws an ApiError with the error body", async () => {
    const response = new Response(null, { status: 409 })
    const error = { code: "conflict", detail: "Modifié entre-temps" }

    await expect(unwrap(Promise.resolve({ error, response }))).rejects.toEqual(
      new ApiError(409, error),
    )
  })
})
