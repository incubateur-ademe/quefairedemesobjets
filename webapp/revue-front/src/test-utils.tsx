import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render } from "@testing-library/react"
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

type Handler = (path: string, options?: { params?: Record<string, unknown> }) => unknown

/** Fake openapi-fetch client: `handler` returns the data of each GET. */
export function fakeApi(handler: Handler) {
  const respond = async (
    path: string,
    options?: { params?: Record<string, unknown> },
  ) => ({
    data: await handler(path, options),
    response: new (class {
      ok = true
      status = 200
    })(),
  })
  return { GET: jest.fn(respond), POST: jest.fn(respond) } as unknown as ApiClient & {
    GET: jest.Mock
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
  element.dispatchEvent(new Event(eventName, { bubbles: true }))
}
