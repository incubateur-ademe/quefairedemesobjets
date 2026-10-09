import { keepPreviousData, useQuery } from "@tanstack/react-query"

import { useApp } from "../context"
import { unwrap } from "./client"
import type { CohortePage, FilterField, LogPage } from "./types"

export type CohortesParams = {
  filtre?: string
  type_action?: string[]
  statut?: string[]
  cree_apres?: string
  cree_avant?: string
  tri?: string
  page: number
  page_size: number
}

export type LogsParams = { niveau?: string[]; page: number; page_size: number }

/** Query keys: one place to invalidate after mutations. */
export const queryKeys = {
  cohortes: (params: CohortesParams) => ["cohortes", params] as const,
  cohortesFilters: ["cohortes-filtres"] as const,
  logs: (cohorteId: number, params: LogsParams) => ["logs", cohorteId, params] as const,
}

export function useCohortes(params: CohortesParams) {
  const { api } = useApp()
  return useQuery({
    queryKey: queryKeys.cohortes(params),
    queryFn: (): Promise<CohortePage> =>
      unwrap(api.GET("/api/suggestions/cohortes", { params: { query: params } })),
    placeholderData: keepPreviousData,
  })
}

export function useCohortesFilterFields() {
  const { api } = useApp()
  return useQuery({
    queryKey: queryKeys.cohortesFilters,
    queryFn: async (): Promise<FilterField[]> =>
      (await unwrap(api.GET("/api/suggestions/cohortes/filtres"))).champs,
    staleTime: 5 * 60_000,
  })
}

export function useLogs(cohorteId: number | null, params: LogsParams) {
  const { api } = useApp()
  return useQuery({
    queryKey: queryKeys.logs(cohorteId ?? 0, params),
    queryFn: (): Promise<LogPage> =>
      unwrap(
        api.GET("/api/suggestions/cohortes/{cohorte_id}/logs", {
          params: { path: { cohorte_id: cohorteId! }, query: params },
        }),
      ),
    enabled: cohorteId !== null,
    placeholderData: keepPreviousData,
  })
}
