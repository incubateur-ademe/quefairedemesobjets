/** Mass actions: preview of the counts, run, then refresh of the groupes shown on
 * the page (decided elements stay on screen). Large reports run as background
 * tasks, followed in the « Tâches » panel: the page is refreshed when one ends. */
import {
  keepPreviousData,
  type QueryClient,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"
import { useEffect, useRef } from "react"

import { useNotifyError } from "../components/common/ErrorToaster"
import { useApp } from "../context"
import { toApiSelection, type ListFilter, type Selection } from "../state/selection"
import { ApiError, unwrap, type ApiClient } from "./client"
import { patchGroupeInCaches } from "./mutations"
import { queryKeys } from "./queries"
import type { Groupe, GroupePage, Tache, Vue } from "./types"

export type MassAction =
  | "validate"
  | "reject"
  | "resubmit"
  | "report_correction"
  | "report_parent"
  | "restore_correction"

export type MassCounts = Record<MassAction, number>

const IN_MAX = 100

export function useMassPreview(
  cohorteId: number,
  vue: Vue,
  selection: Selection,
  list: ListFilter,
  enabled: boolean,
) {
  const { api } = useApp()
  const body = { vue, selection: toApiSelection(selection, list, vue) }
  return useQuery({
    queryKey: ["apercu", cohorteId, body] as const,
    queryFn: async (): Promise<MassCounts> =>
      (
        await unwrap(
          api.POST("/api/suggestions/cohortes/{cohorte_id}/actions/apercu", {
            params: { path: { cohorte_id: cohorteId } },
            body,
          }),
        )
      ).compteurs as MassCounts,
    enabled,
    placeholderData: keepPreviousData,
  })
}

/** Reloads groupes by id (filter « id du groupe parmi », 100 at a time). */
async function fetchGroupes(api: ApiClient, cohorteId: number, ids: number[]) {
  const groupes: Groupe[] = []
  for (let start = 0; start < ids.length; start += IN_MAX) {
    const chunk = ids.slice(start, start + IN_MAX)
    const page: GroupePage = await unwrap(
      api.GET("/api/suggestions/cohortes/{cohorte_id}/groupes", {
        params: {
          path: { cohorte_id: cohorteId },
          query: {
            filtre: JSON.stringify({
              op: "and",
              conditions: [{ field: "groupe.id", operator: "in", value: chunk }],
            }),
            afficher: "tout",
            page: 1,
            page_size: IN_MAX,
          },
        },
      }),
    )
    groupes.push(...page.items)
  }
  return groupes
}

/** Reloads the groupes of the page and patches them in place. */
async function refreshGroupes(
  api: ApiClient,
  queryClient: QueryClient,
  cohorteId: number,
  ids: number[],
) {
  const groupes = await fetchGroupes(api, cohorteId, ids)
  groupes.forEach((groupe) =>
    patchGroupeInCaches(queryClient, cohorteId, groupe.id, () => groupe),
  )
}

/** Counters and previews changed by a mass action or a background task. */
function invalidateCounts(queryClient: QueryClient, cohorteId: number) {
  queryClient.invalidateQueries({ queryKey: queryKeys.stats(cohorteId) })
  queryClient.invalidateQueries({ queryKey: queryKeys.cohorte(cohorteId) })
  queryClient.invalidateQueries({ queryKey: ["apercu", cohorteId] })
  queryClient.invalidateQueries({ queryKey: ["cohortes"] })
}

export function useMassAction(cohorteId: number) {
  const { api } = useApp()
  const queryClient = useQueryClient()
  const notifyError = useNotifyError()

  return useMutation({
    mutationFn: async ({
      vue,
      action,
      selection,
      list,
      pageGroupeIds,
    }: {
      vue: Vue
      action: MassAction
      selection: Selection
      list: ListFilter
      pageGroupeIds: number[]
    }) => {
      const { data, error, response } = await api.POST(
        "/api/suggestions/cohortes/{cohorte_id}/actions",
        {
          params: { path: { cohorte_id: cohorteId } },
          body: { vue, action, selection: toApiSelection(selection, list, vue) },
        },
      )
      if (!response.ok) {
        throw new ApiError(response.status, (error ?? {}) as ApiError["body"])
      }
      if (response.status === 202) {
        // Background task: followed by useTaches, which refreshes the page
        queryClient.invalidateQueries({ queryKey: queryKeys.taches(cohorteId) })
        return data
      }
      // The decided elements stay on screen until the list changes
      await refreshGroupes(api, queryClient, cohorteId, pageGroupeIds)
      return data
    },
    onError: (error) => notifyError(`Action de masse : ${error.message}`),
    onSettled: () => invalidateCounts(queryClient, cohorteId),
  })
}

const POLL_MS = 2000

export const isActive = (tache: Tache) =>
  tache.statut === "pending" || tache.statut === "running"

/** Background tasks of the cohorte, polled while one is pending or running. When
 * one ends, the groupes of the page (`pageGroupeIds`) and the counters are
 * reloaded; a failure is notified. */
export function useTaches(cohorteId: number, pageGroupeIds: number[]) {
  const { api } = useApp()
  const queryClient = useQueryClient()
  const notifyError = useNotifyError()
  const query = useQuery({
    queryKey: queryKeys.taches(cohorteId),
    queryFn: (): Promise<Tache[]> =>
      unwrap(
        api.GET("/api/suggestions/cohortes/{cohorte_id}/taches", {
          params: { path: { cohorte_id: cohorteId } },
        }),
      ),
    refetchInterval: (query) => (query.state.data?.some(isActive) ? POLL_MS : false),
  })

  const page = useRef(pageGroupeIds)
  useEffect(() => {
    page.current = pageGroupeIds
  })
  const active = useRef<Set<string> | null>(null)
  useEffect(() => {
    if (!query.data) {
      return
    }
    const ended = query.data.filter(
      (tache) => active.current?.has(tache.id) && !isActive(tache),
    )
    active.current = new Set(query.data.filter(isActive).map((tache) => tache.id))
    if (!ended.length) {
      return
    }
    if (ended.some((tache) => tache.statut === "error")) {
      notifyError("Le report en tâche de fond a échoué : voir le panneau Tâches")
    }
    invalidateCounts(queryClient, cohorteId)
    refreshGroupes(api, queryClient, cohorteId, page.current).catch((error) =>
      notifyError(error.message),
    )
  }, [query.data, api, queryClient, cohorteId, notifyError])
  return query
}
