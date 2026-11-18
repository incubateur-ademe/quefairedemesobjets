/** Writes of the review screen: optimistic, rolled back on error.
 *
 * Every write returns the whole groupe, which replaces it in every cached page
 * (it also brings the automatic switch of the groupe to ATRAITER). Pages are never
 * refetched after a write: decided items stay on screen until the list changes.
 * Only errors are notified (409: the groupe is reloaded from the server answer).
 */
import { useMutation, useQueryClient, type QueryClient } from "@tanstack/react-query"
import { useRef } from "react"

import { useNotifyError } from "../components/common/ErrorToaster"
import { useApp } from "../context"
import { ApiError, unwrap } from "./client"
import { queryKeys } from "./queries"
import type {
  Groupe,
  GroupeDetail,
  GroupePage,
  Ligne,
  LignePage,
  Modele,
} from "./types"

type Snapshot = [readonly unknown[], unknown][]

export function patchGroupeInCaches(
  queryClient: QueryClient,
  cohorteId: number,
  groupeId: number,
  update: (groupe: Groupe) => Groupe,
) {
  // The modal of the groupe shows the same lignes
  queryClient.setQueryData<GroupeDetail>(
    queryKeys.groupe(groupeId),
    (detail) => detail && { ...detail, ...update(detail) },
  )
  queryClient.setQueriesData<LignePage>(
    { queryKey: queryKeys.lignes(cohorteId) },
    (page) =>
      page && {
        ...page,
        groupes: page.groupes.map((groupe) =>
          groupe.id === groupeId ? update(groupe) : groupe,
        ),
      },
  )
  queryClient.setQueriesData<GroupePage>(
    { queryKey: queryKeys.groupes(cohorteId) },
    (page) =>
      page && {
        ...page,
        items: page.items.map((groupe) =>
          groupe.id === groupeId ? update(groupe) : groupe,
        ),
      },
  )
}

const NO_GROUPE_ACTION = {
  valider: false,
  refuser: false,
  remettre_a_valider: false,
  reporter_correction: false,
  reporter_parent: false,
}

/** Value emptying a field of the acteur (EMPTY_ACTEUR_FIELD in Django) */
const EMPTY_VALUE = "__empty__"

const NO_LIGNE_ACTION: Ligne["capacites"] = {
  valider: false,
  remettre_a_valider: false,
  remettre_groupe_a_valider: false,
  corriger_correction: false,
  corriger_parent: false,
  reporter_correction: false,
  reporter_parent: false,
  restaurer_correction: false,
  supprimer_correction: false,
  supprimer_parent: false,
}

/** Optimistic state: new statut, actions disabled until the server answers. */
export function withStatut(groupe: Groupe, statut: string, lignes?: string[]): Groupe {
  const touched = (ligne: Ligne) => !lignes || lignes.includes(ligne.key)
  const nextLignes = groupe.lignes.map((ligne) =>
    touched(ligne) ? { ...ligne, statut, capacites: NO_LIGNE_ACTION } : ligne,
  )
  return {
    ...groupe,
    statut: lignes ? groupe.statut : statut,
    lignes: nextLignes,
    lignes_validees: nextLignes.filter((ligne) => ligne.statut === "ATRAITER").length,
    capacites: lignes ? groupe.capacites : NO_GROUPE_ACTION,
  }
}

export function withProposition(
  groupe: Groupe,
  ligneKey: string,
  modele: Modele,
  propose: Record<string, string> | null,
): Groupe {
  const column = modele === "RevisionActeur" ? "correction" : "parent"
  return {
    ...groupe,
    lignes: groupe.lignes.map((ligne) => {
      const cell = ligne[column]
      return ligne.key === ligneKey && cell
        ? { ...ligne, [column]: { ...cell, propose, etat: "valeur" as const } }
        : ligne
    }),
  }
}

export function withReport(
  groupe: Groupe,
  modele: Modele,
  ligneKeys?: string[],
): Groupe {
  const capacity =
    modele === "RevisionActeur" ? "reporter_correction" : "reporter_parent"
  return groupe.lignes
    .filter(
      (ligne) =>
        ligne.capacites[capacity] && (!ligneKeys || ligneKeys.includes(ligne.key)),
    )
    .reduce(
      (current, ligne) =>
        withProposition(current, ligne.key, modele, ligne.acteur.propose),
      groupe,
    )
}

/** Optimistic correction with the current value of the acteur (« __empty__ »
 * when empty) on the restorable lignes whose value is known. */
export function withRestauration(groupe: Groupe, ligneKeys?: string[]): Groupe {
  return groupe.lignes
    .filter(
      (ligne) =>
        ligne.capacites.restaurer_correction &&
        ligne.acteur.actuel &&
        (!ligneKeys || ligneKeys.includes(ligne.key)),
    )
    .reduce(
      (current, ligne) =>
        withProposition(
          current,
          ligne.key,
          "RevisionActeur",
          Object.fromEntries(
            Object.entries(ligne.acteur.actuel ?? {}).map(([champ, valeur]) => [
              champ,
              valeur || EMPTY_VALUE,
            ]),
          ),
        ),
      groupe,
    )
}

type Write = {
  groupe: Groupe
  /** Receives the last known `modifie_le` of the groupe */
  request: (expectedModifieLe: string) => Promise<Groupe>
  optimistic: (groupe: Groupe) => Groupe
}

/** One hook for every write on a groupe. */
/** Last `modifie_le` of a groupe known from the server (cached pages or detail):
 * optimistic updates keep it, server answers update it. */
function lastModifieLe(queryClient: QueryClient, cohorteId: number, groupe: Groupe) {
  const detail = queryClient.getQueryData<GroupeDetail>(queryKeys.groupe(groupe.id))
  if (detail) {
    return detail.modifie_le
  }
  for (const [, page] of queryClient
    .getQueriesData<GroupePage | LignePage>({
      queryKey: queryKeys.groupes(cohorteId),
    })
    .concat(
      queryClient.getQueriesData<GroupePage | LignePage>({
        queryKey: queryKeys.lignes(cohorteId),
      }),
    )) {
    const groupes = page && ("groupes" in page ? page.groupes : page.items)
    const found = groupes?.find((g) => g.id === groupe.id)
    if (found) {
      return found.modifie_le
    }
  }
  return groupe.modifie_le
}

export function useGroupeWrite(cohorteId: number) {
  const queryClient = useQueryClient()
  const notifyError = useNotifyError()
  // Writes on a same groupe run one after the other, each with the `modifie_le`
  // answered by the previous one: chained decisions (A, A, A…) do not conflict
  const queues = useRef(new Map<number, Promise<Groupe>>())

  return useMutation<Groupe, Error, Write, Snapshot>({
    mutationFn: ({ groupe, request }) => {
      const previous: Promise<Groupe | undefined> =
        queues.current.get(groupe.id) ?? Promise.resolve(undefined)
      const run = previous
        // After a conflict, the server gives the current groupe
        .catch((error) =>
          error instanceof ApiError
            ? (error.body.current as Groupe | undefined)
            : undefined,
        )
        .then((last) =>
          request(last?.modifie_le ?? lastModifieLe(queryClient, cohorteId, groupe)),
        )
      queues.current.set(groupe.id, run)
      return run
    },
    onMutate: async ({ groupe, optimistic }) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.groupes(cohorteId) })
      await queryClient.cancelQueries({ queryKey: queryKeys.lignes(cohorteId) })
      await queryClient.cancelQueries({ queryKey: queryKeys.groupe(groupe.id) })
      const snapshot: Snapshot = [
        ...queryClient.getQueriesData({ queryKey: queryKeys.groupes(cohorteId) }),
        ...queryClient.getQueriesData({ queryKey: queryKeys.lignes(cohorteId) }),
        [
          queryKeys.groupe(groupe.id),
          queryClient.getQueryData(queryKeys.groupe(groupe.id)),
        ],
      ]
      patchGroupeInCaches(queryClient, cohorteId, groupe.id, optimistic)
      return snapshot
    },
    onSuccess: (groupe) =>
      patchGroupeInCaches(queryClient, cohorteId, groupe.id, () => groupe),
    onError: (error, { groupe }, snapshot) => {
      snapshot?.forEach(([key, data]) => queryClient.setQueryData(key, data))
      if (error instanceof ApiError && error.body.current) {
        const current = error.body.current as Groupe
        patchGroupeInCaches(queryClient, cohorteId, groupe.id, () => current)
      }
      // Validation errors of a correction are shown on the field by the editor
      if (!(error instanceof ApiError && error.status === 422 && error.body.errors)) {
        notifyError(`Groupe ${groupe.id} : ${error.message}`)
      }
    },
    onSettled: (_data, _error, { groupe }) => {
      // Map points and identifiers of the modal depend on the propositions
      queryClient.invalidateQueries({ queryKey: queryKeys.groupe(groupe.id) })
      queryClient.invalidateQueries({ queryKey: queryKeys.stats(cohorteId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.cohorte(cohorteId) })
      queryClient.invalidateQueries({ queryKey: ["cohortes"] })
    },
  })
}

/** Builders of the requests, returning the updated groupe. */
export function useGroupeActions(cohorteId: number) {
  const { api } = useApp()
  const write = useGroupeWrite(cohorteId)
  const path = (groupe: Groupe) => ({ path: { groupe_id: groupe.id } })
  const expected = (modifieLe: string) => ({ expected_modifie_le: modifieLe })
  const champsOf = (groupe: Groupe, keys: string[]) =>
    groupe.lignes
      .filter((ligne) => keys.includes(ligne.key))
      .map((ligne) => ligne.champs)

  return {
    pending: write.isPending,
    decideGroupe: (groupe: Groupe, action: "validate" | "reject" | "resubmit") =>
      write.mutateAsync({
        groupe,
        optimistic: (g) =>
          withStatut(
            g,
            action === "validate"
              ? "ATRAITER"
              : action === "reject"
                ? "REJETEE"
                : "AVALIDER",
          ),
        request: (modifieLe) =>
          unwrap(
            api.POST("/api/suggestions/groupes/{groupe_id}/decision", {
              params: path(groupe),
              body: { action, ...expected(modifieLe) },
            }),
          ),
      }),
    decideLignes: (groupe: Groupe, keys: string[], action: "validate" | "resubmit") =>
      write.mutateAsync({
        groupe,
        optimistic: (g) =>
          action === "resubmit" && g.statut === "REJETEE"
            ? withStatut(g, "AVALIDER")
            : withStatut(g, action === "validate" ? "ATRAITER" : "AVALIDER", keys),
        request: (modifieLe) =>
          unwrap(
            api.POST("/api/suggestions/groupes/{groupe_id}/lignes/decision", {
              params: path(groupe),
              body: { champs: champsOf(groupe, keys), action, ...expected(modifieLe) },
            }),
          ),
      }),
    upsertProposition: (
      groupe: Groupe,
      // The ligne may not exist yet (new correction of the localisation)
      ligne: Pick<Ligne, "key" | "champs">,
      modele: Modele,
      valeurs: Record<string, string>,
    ) =>
      write.mutateAsync({
        groupe,
        optimistic: (g) => withProposition(g, ligne.key, modele, valeurs),
        request: (modifieLe) =>
          unwrap(
            api.PUT("/api/suggestions/groupes/{groupe_id}/propositions", {
              params: path(groupe),
              body: {
                suggestion_modele: modele,
                champs: ligne.champs,
                valeurs,
                ...expected(modifieLe),
              },
            }),
          ),
      }),
    deleteProposition: (groupe: Groupe, ligne: Ligne, modele: Modele) =>
      write.mutateAsync({
        groupe,
        optimistic: (g) => withProposition(g, ligne.key, modele, null),
        request: (modifieLe) =>
          unwrap(
            api.DELETE("/api/suggestions/groupes/{groupe_id}/propositions", {
              params: {
                ...path(groupe),
                query: {
                  suggestion_modele: modele,
                  champs: ligne.champs,
                  ...expected(modifieLe),
                },
              },
            }),
          ),
      }),
    report: (groupe: Groupe, modele: Modele, keys?: string[]) =>
      write.mutateAsync({
        groupe,
        optimistic: (g) => withReport(g, modele, keys),
        request: (modifieLe) =>
          unwrap(
            api.POST("/api/suggestions/groupes/{groupe_id}/report", {
              params: path(groupe),
              body: {
                cible: modele === "RevisionActeur" ? "correction" : "parent",
                champs: keys ? champsOf(groupe, keys) : null,
                ...expected(modifieLe),
              },
            }),
          ),
      }),
    restaurer: (groupe: Groupe, keys?: string[]) =>
      write.mutateAsync({
        groupe,
        optimistic: (g) => withRestauration(g, keys),
        request: (modifieLe) =>
          unwrap(
            api.POST("/api/suggestions/groupes/{groupe_id}/restaurer", {
              params: path(groupe),
              body: {
                champs: keys ? champsOf(groupe, keys) : null,
                ...expected(modifieLe),
              },
            }),
          ),
      }),
  }
}

export type GroupeActions = ReturnType<typeof useGroupeActions>
