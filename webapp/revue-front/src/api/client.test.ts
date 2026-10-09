/**
 * @jest-environment node
 */
import { ApiError, createCsrfMiddleware, readCookie, unwrap } from "./client"

describe("readCookie", () => {
  it("reads a cookie among others", () => {
    expect(readCookie("csrftoken", "a=1; csrftoken=abc; b=2")).toBe("abc")
    expect(readCookie("csrftoken", "a=1")).toBeUndefined()
  })
})

describe("csrfMiddleware", () => {
  const run = (method: string) => {
    const middleware = createCsrfMiddleware(() => "a=1; csrftoken=token123")
    const request = new Request("http://localhost/api/suggestions/me", { method })
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return (middleware.onRequest as any)({ request }) as Request
  }

  it.each(["POST", "PUT", "PATCH", "DELETE"])("sets the token on %s", (method) => {
    expect(run(method).headers.get("X-CSRFToken")).toBe("token123")
  })

  it("does not set the token on GET", () => {
    expect(run("GET").headers.get("X-CSRFToken")).toBeNull()
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
