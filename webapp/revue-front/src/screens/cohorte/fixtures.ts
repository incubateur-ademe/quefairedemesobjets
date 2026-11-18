import type { CohorteDetail, Groupe, GroupePage, Ligne, Stats } from "../../api/types"

const NONE = {
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

export function ligne(
  groupeId: number,
  champs: string[],
  patch: Partial<Ligne> = {},
): Ligne {
  return {
    key: `${groupeId}:${champs.join(",")}`,
    champs,
    statut: "AVALIDER",
    decision_par: null,
    decision_le: null,
    acteur: {
      actuel: Object.fromEntries(champs.map((c) => [c, `${c} actuel`])),
      propose: Object.fromEntries(champs.map((c) => [c, `${c} source`])),
      etat: "valeur",
    },
    correction: { actuel: null, propose: null, etat: "pas_de_correction" },
    parent: null,
    capacites: {
      ...NONE,
      valider: true,
      corriger_correction: true,
      reporter_correction: true,
    },
    ...patch,
  }
}

export function groupe(id: number, patch: Partial<Groupe> = {}): Groupe {
  const lignes = [ligne(id, ["nom"]), ligne(id, ["url"])]
  return {
    id,
    statut: "AVALIDER",
    modifie_le: "2026-10-09T10:00:00.000Z",
    decision_par: null,
    decision_le: null,
    acteur: {
      identifiant_unique: `acteur_${id}`,
      identifiant_externe: `ext_${id}`,
      nom: `Acteur ${id}`,
      ville: "Lyon",
      admin_urls: {
        importe: `/admin/qfdmo/acteur/acteur_${id}/change/`,
        affiche: null,
        corrige: null,
        parent: null,
      },
    },
    is_new: false,
    has_correction: false,
    parent: null,
    lignes,
    lignes_validees: 0,
    lignes_total: lignes.length,
    capacites: {
      valider: true,
      refuser: true,
      remettre_a_valider: false,
      reporter_correction: true,
      reporter_parent: false,
    },
    ...patch,
  }
}

export const page = (items: Groupe[]): GroupePage => ({
  items,
  total: items.length,
  page: 1,
  page_size: 100,
})

export const COHORTE: CohorteDetail = {
  id: 7,
  identifiant_action: "dag_ecomaison",
  identifiant_execution: "manual__2026-10-01T06:00:00",
  execution_datetime: "01/10/2026 06:00",
  type_action: "SOURCE_MODIFICATION",
  type_action_label: "modification",
  statut: "AVALIDER",
  cree_le: "2026-10-01T06:00:00Z",
  metadata: null,
  total_groupes: 2,
  compteurs: { AVALIDER: 2, ATRAITER: 0, REJETEE: 0, ENCOURS: 0, SUCCES: 0, ERREUR: 0 },
  logs: { ERROR: 0, WARNING: 0, INFO: 0 },
  policy: {
    type_action: "SOURCE_MODIFICATION",
    has_lines: true,
    can_reject_line: false,
    can_reject_group: true,
    editable_models: ["RevisionActeur", "ParentRevisionActeur"],
    shows_parent: true,
    shows_acteur_diff: true,
    badge: null,
  },
}

export const STATS: Stats = {
  compteurs: { AVALIDER: 2, ATRAITER: 0, REJETEE: 0, ENCOURS: 0, SUCCES: 0, ERREUR: 0 },
  totaux_vues: { groupes: 2, lignes: 4 },
  tuples: [
    { champs: ["nom"], count: 2 },
    { champs: ["url"], count: 2 },
  ],
}
