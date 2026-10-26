import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { fireEvent, render } from "@testing-library/react"
import type { ReactNode } from "react"

import type { ApiClient } from "./api/client"
import type { Bootstrap } from "./bootstrap"
import { ErrorToaster } from "./components/common/ErrorToaster"
import { AppContext } from "./context"
import { RouterProvider } from "./router"

export const BOOTSTRAP: Bootstrap = {
  basepath: "/data/revue/",
  apiBase: "/api/suggestions",
  adminBase: "/admin/",
  environment: "test",
  user: { id: 1, username: "admin" },
}

/** Error answered by the fake API (status and JSON body). */
export class FakeApiError {
  constructor(
    readonly status: number,
    readonly body: Record<string, unknown>,
  ) {}
}

type Handler = (
  path: string,
  options: { params?: Record<string, unknown>; body?: unknown } | undefined,
  method: "GET" | "POST" | "PUT" | "DELETE",
) => unknown

/** Fake openapi-fetch client: `handler` returns the data of each request, or a
 * FakeApiError. */
export function fakeApi(handler: Handler) {
  const respond =
    (method: "GET" | "POST" | "PUT" | "DELETE") =>
    async (
      path: string,
      options?: { params?: Record<string, unknown>; body?: unknown },
    ) => {
      const result = await handler(path, options, method)
      if (result instanceof FakeApiError) {
        return { error: result.body, response: { ok: false, status: result.status } }
      }
      return { data: result, response: { ok: true, status: 200 } }
    }
  return {
    GET: jest.fn(respond("GET")),
    POST: jest.fn(respond("POST")),
    PUT: jest.fn(respond("PUT")),
    DELETE: jest.fn(respond("DELETE")),
  } as unknown as ApiClient & {
    GET: jest.Mock
    POST: jest.Mock
    PUT: jest.Mock
    DELETE: jest.Mock
  }
}

export function renderApp(
  ui: ReactNode,
  { api, url }: { api: ApiClient; url: string },
) {
  window.history.replaceState(null, "", url)
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <AppContext.Provider value={{ bootstrap: BOOTSTRAP, api }}>
      <QueryClientProvider client={queryClient}>
        <ErrorToaster>
          <RouterProvider basepath={BOOTSTRAP.basepath}>{ui}</RouterProvider>
        </ErrorToaster>
      </QueryClientProvider>
    </AppContext.Provider>,
  )
}

/** Sets the value of a (mocked) Web Awesome control and fires its event. */
export function setControlValue(
  element: Element,
  value: string | string[],
  eventName: "change" | "input" = "change",
) {
  ;(element as HTMLElement & { value: unknown }).value = value
  // fireEvent wraps the dispatch in act(): state updates are flushed
  fireEvent(element, new Event(eventName, { bubbles: true }))
}
