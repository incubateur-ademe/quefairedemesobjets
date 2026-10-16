/** Mass actions: preview of the counts, run, follow-up of background jobs, then
 * refresh of the groupes shown on the page (decided elements stay on screen). */
import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"
import { useState } from "react"

import { useNotifyError } from "../components/common/ErrorToaster"
import { useApp } from "../context"
import { toApiSelection, type ListFilter, type Selection } from "../state/selection"
import { ApiError, unwrap, type ApiClient } from "./client"
import { patchGroupeInCaches } from "./mutations"
import { queryKeys } from "./queries"
import type { Groupe, GroupePage, Vue } from "./types"

export type MassAction =
  "validate" | "reject" | "resubmit" | "report_correction" | "report_parent"

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

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

export function useMassAction(cohorteId: number) {
  const { api } = useApp()
  const queryClient = useQueryClient()
  const notifyError = useNotifyError()
  const [job, setJob] = useState<{ total: number } | null>(null)

  const mutation = useMutation({
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
      if (response.status === 202 && data && "job_id" in data) {
        setJob({ total: data.total })
        try {
          await waitForJob(api, data.job_id)
        } finally {
          setJob(null)
        }
      }
      // The groupes of the page are reloaded and patched in place: the decided
      // elements stay on screen until the list changes
      const groupes = await fetchGroupes(api, cohorteId, pageGroupeIds)
      groupes.forEach((groupe) =>
        patchGroupeInCaches(queryClient, cohorteId, groupe.id, () => groupe),
      )
      return data
    },
    onError: (error) => notifyError(`Action de masse : ${error.message}`),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.stats(cohorteId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.cohorte(cohorteId) })
      queryClient.invalidateQueries({ queryKey: ["apercu", cohorteId] })
      queryClient.invalidateQueries({ queryKey: ["cohortes"] })
    },
  })
  return { ...mutation, job }
}

async function waitForJob(api: ApiClient, jobId: string) {
  for (;;) {
    await sleep(1000)
    const status = await unwrap(
      api.GET("/api/suggestions/jobs/{job_id}", {
        params: { path: { job_id: jobId } },
      }),
    )
    if (status.status === "done") {
      return status
    }
    if (status.status === "error") {
      throw new Error("le report en tâche de fond a échoué")
    }
  }
}
