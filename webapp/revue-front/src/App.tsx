import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useState } from "react"

import { createApiClient } from "./api/client"
import type { Bootstrap } from "./bootstrap"
import { ErrorToaster } from "./components/common/ErrorToaster"
import { AppContext } from "./context"
import { RouterProvider } from "./router"
import { Routes } from "./Routes"

export function App({ bootstrap }: { bootstrap: Bootstrap }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
      }),
  )
  const [api] = useState(() => createApiClient(`${bootstrap.adminBase}login/`))

  return (
    <AppContext.Provider value={{ bootstrap, api }}>
      <QueryClientProvider client={queryClient}>
        <ErrorToaster>
          <RouterProvider basepath={bootstrap.basepath}>
            <Routes />
          </RouterProvider>
        </ErrorToaster>
      </QueryClientProvider>
    </AppContext.Provider>
  )
}
