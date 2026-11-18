import { createContext, useContext } from "react"

import type { ApiClient } from "./api/client"
import type { Bootstrap } from "./bootstrap"

export type AppContextValue = { bootstrap: Bootstrap; api: ApiClient }

export const AppContext = createContext<AppContextValue | null>(null)

export function useApp(): AppContextValue {
  const value = useContext(AppContext)
  if (!value) {
    throw new Error("useApp must be used inside <AppContext.Provider>")
  }
  return value
}
