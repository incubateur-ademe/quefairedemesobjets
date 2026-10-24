/** Writes of the review screen: optimistic, rolled back on error.
 *
 * Every write returns the whole groupe, which replaces it in every cached page
 * (it also brings the automatic switch of the groupe to ATRAITER). Pages are never
 * refetched after a write: decided items stay on screen until the list changes.
 * Only errors are notified (409: the groupe is reloaded from the server answer).
 */
import { useMutation, useQueryClient, type QueryClient } from "@tanstack/react-query"

import { useNotifyError } from "../components/common/ErrorToaster"
import { useApp } from "../context"
import { ApiError, unwrap } from "./client"
import { queryKeys } from "./queries"
import type { Groupe, GroupePage, Ligne, Modele } from "./types"

type Snapshot = [readonly unknown[], GroupePage | undefined][]

export function patchGroupeInCaches(
  queryClient: QueryClient,
  cohorteId: number,
  groupeId: number,
  update: (groupe: Groupe) => Groupe,
) {
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

const NO_LIGNE_ACTION: Ligne["capacites"] = {
  valider: false,
  remettre_a_valider: false,
  remettre_groupe_a_valider: false,
  corriger_correction: false,
  corriger_parent: false,
  reporter_correction: false,
  reporter_parent: false,
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

type Write = {
  groupe: Groupe
  request: () => Promise<Groupe>
  optimistic: (groupe: Groupe) => Groupe
}

/** One hook for every write on a groupe. */
export function useGroupeWrite(cohorteId: number) {
  const queryClient = useQueryClient()
  const notifyError = useNotifyError()

  return useMutation<Groupe, Error, Write, Snapshot>({
    mutationFn: ({ request }) => request(),
    onMutate: async ({ groupe, optimistic }) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.groupes(cohorteId) })
      const snapshot = queryClient.getQueriesData<GroupePage>({
        queryKey: queryKeys.groupes(cohorteId),
      })
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
    onSettled: () => {
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
  const expected = (groupe: Groupe) => ({ expected_modifie_le: groupe.modifie_le })
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
        request: () =>
          unwrap(
            api.POST("/api/suggestions/groupes/{groupe_id}/decision", {
              params: path(groupe),
              body: { action, ...expected(groupe) },
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
        request: () =>
          unwrap(
            api.POST("/api/suggestions/groupes/{groupe_id}/lignes/decision", {
              params: path(groupe),
              body: { champs: champsOf(groupe, keys), action, ...expected(groupe) },
            }),
          ),
      }),
    upsertProposition: (
      groupe: Groupe,
      ligne: Ligne,
      modele: Modele,
      valeurs: Record<string, string>,
    ) =>
      write.mutateAsync({
        groupe,
        optimistic: (g) => withProposition(g, ligne.key, modele, valeurs),
        request: () =>
          unwrap(
            api.PUT("/api/suggestions/groupes/{groupe_id}/propositions", {
              params: path(groupe),
              body: {
                suggestion_modele: modele,
                champs: ligne.champs,
                valeurs,
                ...expected(groupe),
              },
            }),
          ),
      }),
    deleteProposition: (groupe: Groupe, ligne: Ligne, modele: Modele) =>
      write.mutateAsync({
        groupe,
        optimistic: (g) => withProposition(g, ligne.key, modele, null),
        request: () =>
          unwrap(
            api.DELETE("/api/suggestions/groupes/{groupe_id}/propositions", {
              params: {
                ...path(groupe),
                query: {
                  suggestion_modele: modele,
                  champs: ligne.champs,
                  ...expected(groupe),
                },
              },
            }),
          ),
      }),
    report: (groupe: Groupe, modele: Modele, keys?: string[]) =>
      write.mutateAsync({
        groupe,
        optimistic: (g) => withReport(g, modele, keys),
        request: () =>
          unwrap(
            api.POST("/api/suggestions/groupes/{groupe_id}/report", {
              params: path(groupe),
              body: {
                cible: modele === "RevisionActeur" ? "correction" : "parent",
                champs: keys ? champsOf(groupe, keys) : null,
                ...expected(groupe),
              },
            }),
          ),
      }),
  }
}

export type GroupeActions = ReturnType<typeof useGroupeActions>
