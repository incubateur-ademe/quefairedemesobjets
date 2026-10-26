import { keepPreviousData, useQuery } from "@tanstack/react-query"

import { useApp } from "../context"
import { unwrap } from "./client"
import type {
  Afficher,
  ChampChoix,
  CohorteDetail,
  AnnuaireEntreprise,
  CohortePage,
  FilterField,
  GroupeDetail,
  GroupePage,
  LignePage,
  LogPage,
  Stats,
  Vue,
} from "./types"

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

/** Filters shared by both views of a cohorte. */
export type RevueParams = { filtre?: string; tuples?: string[]; afficher: Afficher }

export type GroupesParams = RevueParams & { page: number; page_size: number }

/** Query keys: one place to invalidate after mutations. */
export const queryKeys = {
  cohortes: (params: CohortesParams) => ["cohortes", params] as const,
  cohortesFilters: ["cohortes-filtres"] as const,
  logs: (cohorteId: number, params: LogsParams) => ["logs", cohorteId, params] as const,
  cohorte: (cohorteId: number) => ["cohorte", cohorteId] as const,
  taches: (cohorteId: number) => ["taches", cohorteId] as const,
  champsChoix: ["champs-choix"] as const,
  reviewFilters: (cohorteId: number) => ["revue-filtres", cohorteId] as const,
  groupes: (cohorteId: number, params?: GroupesParams) =>
    params
      ? (["groupes", cohorteId, params] as const)
      : (["groupes", cohorteId] as const),
  lignes: (cohorteId: number, params?: GroupesParams) =>
    params
      ? (["lignes", cohorteId, params] as const)
      : (["lignes", cohorteId] as const),
  groupe: (groupeId: number) => ["groupe", groupeId] as const,
  stats: (cohorteId: number, params?: RevueParams & { vue: Vue }) =>
    params ? (["stats", cohorteId, params] as const) : (["stats", cohorteId] as const),
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

/** Values of the fields edited with a select: they do not change during a session. */
export function useChampsChoix() {
  const { api } = useApp()
  return useQuery({
    queryKey: queryKeys.champsChoix,
    queryFn: (): Promise<Record<string, ChampChoix>> =>
      unwrap(api.GET("/api/suggestions/champs/choix")),
    staleTime: Infinity,
  })
}

export function useCohorte(cohorteId: number) {
  const { api } = useApp()
  return useQuery({
    queryKey: queryKeys.cohorte(cohorteId),
    queryFn: (): Promise<CohorteDetail> =>
      unwrap(
        api.GET("/api/suggestions/cohortes/{cohorte_id}", {
          params: { path: { cohorte_id: cohorteId } },
        }),
      ),
  })
}

export function useReviewFilterFields(cohorteId: number) {
  const { api } = useApp()
  return useQuery({
    queryKey: queryKeys.reviewFilters(cohorteId),
    queryFn: async (): Promise<FilterField[]> =>
      (
        await unwrap(
          api.GET("/api/suggestions/cohortes/{cohorte_id}/revue/filtres", {
            params: { path: { cohorte_id: cohorteId } },
          }),
        )
      ).champs,
    staleTime: 5 * 60_000,
  })
}

/** Page of groupes. Never refetched after a decision: the cache is patched in
 * place so that decided groupes stay on screen until the list changes. */
export function useGroupesPage(
  cohorteId: number,
  params: GroupesParams,
  enabled = true,
) {
  const { api } = useApp()
  return useQuery({
    queryKey: queryKeys.groupes(cohorteId, params),
    queryFn: (): Promise<GroupePage> =>
      unwrap(
        api.GET("/api/suggestions/cohortes/{cohorte_id}/groupes", {
          params: { path: { cohorte_id: cohorteId }, query: params },
        }),
      ),
    staleTime: Infinity,
    placeholderData: keepPreviousData,
    enabled,
  })
}

export function useStats(cohorteId: number, params: RevueParams & { vue: Vue }) {
  const { api } = useApp()
  return useQuery({
    queryKey: queryKeys.stats(cohorteId, params),
    queryFn: (): Promise<Stats> =>
      unwrap(
        api.GET("/api/suggestions/cohortes/{cohorte_id}/stats", {
          params: { path: { cohorte_id: cohorteId }, query: params },
        }),
      ),
    placeholderData: keepPreviousData,
  })
}

/** Detail of a groupe, for the modal (acteur displayed, map, Annuaire). */
export function useGroupeDetail(groupeId: number | null) {
  const { api } = useApp()
  return useQuery({
    queryKey: queryKeys.groupe(groupeId ?? 0),
    queryFn: (): Promise<GroupeDetail> =>
      unwrap(
        api.GET("/api/suggestions/groupes/{groupe_id}", {
          params: { path: { groupe_id: groupeId! } },
        }),
      ),
    enabled: groupeId !== null,
  })
}

/** Entreprise and établissement of a SIRET / SIREN (Annuaire des entreprises). */
export function useAnnuaireEntreprise(
  champ: "siret" | "siren",
  valeur: string,
  enabled = true,
) {
  const { api } = useApp()
  return useQuery({
    queryKey: ["annuaire", champ, valeur] as const,
    queryFn: (): Promise<AnnuaireEntreprise> =>
      unwrap(
        api.GET("/api/suggestions/annuaire-entreprises", {
          params: { query: { champ, valeur } },
        }),
      ),
    staleTime: 60 * 60_000,
    retry: false,
    enabled: enabled && Boolean(valeur),
  })
}

/** Page of lignes: references to lignes, found in their groupes. Never refetched
 * after a decision, like the pages of groupes. */
export function useLignesPage(
  cohorteId: number,
  params: GroupesParams,
  enabled = true,
) {
  const { api } = useApp()
  return useQuery({
    queryKey: queryKeys.lignes(cohorteId, params),
    queryFn: (): Promise<LignePage> =>
      unwrap(
        api.GET("/api/suggestions/cohortes/{cohorte_id}/lignes", {
          params: { path: { cohorte_id: cohorteId }, query: params },
        }),
      ),
    staleTime: Infinity,
    placeholderData: keepPreviousData,
    enabled,
  })
}
