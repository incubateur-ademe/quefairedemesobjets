import createClient, { type Middleware } from "openapi-fetch"

import type { paths } from "./schema"

/** Error returned by the API: `{ code, detail, errors?, current? }`. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly body: {
      code?: string
      detail?: string
      errors?: Record<string, string[]>
      current?: unknown
    },
  ) {
    super(body.detail ?? `HTTP ${status}`)
  }
}

const UNSAFE_METHODS = ["POST", "PUT", "PATCH", "DELETE"]

export function readCookie(name: string, cookies: string = document.cookie) {
  return cookies
    .split(";")
    .map((cookie) => cookie.trim())
    .find((cookie) => cookie.startsWith(`${name}=`))
    ?.slice(name.length + 1)
}

export function createCsrfMiddleware(
  getCookies: () => string = () => document.cookie,
): Middleware {
  return {
    onRequest({ request }) {
      if (UNSAFE_METHODS.includes(request.method)) {
        request.headers.set("X-CSRFToken", readCookie("csrftoken", getCookies()) ?? "")
      }
      return request
    },
  }
}

export function createApiClient(loginUrl: string) {
  const client = createClient<paths>({ credentials: "same-origin" })
  client.use(createCsrfMiddleware())
  client.use({
    onResponse({ response }) {
      if (response.status === 401) {
        // Session expired: back to the admin login, then here
        window.location.assign(
          `${loginUrl}?next=${encodeURIComponent(window.location.pathname)}`,
        )
      }
      return response
    },
  })
  return client
}

export type ApiClient = ReturnType<typeof createApiClient>

/** Unwraps an openapi-fetch result: returns the data or throws an ApiError. */
export async function unwrap<T>(
  promise: Promise<{ data?: T; error?: unknown; response: Response }>,
): Promise<T> {
  const { data, error, response } = await promise
  if (!response.ok) {
    throw new ApiError(response.status, (error ?? {}) as ApiError["body"])
  }
  return data as T
}
