/** Labels and colors of statuts and log levels (colors: classes p-*, bg-*, c-*). */
export type Tone = "warn" | "ok" | "danger" | "info" | "done" | "err"

export const STATUT_ORDER = [
  "AVALIDER",
  "ATRAITER",
  "REJETEE",
  "ENCOURS",
  "SUCCES",
  "ERREUR",
] as const

export type Statut = (typeof STATUT_ORDER)[number]

export const STATUTS: Record<Statut, { label: string; tone: Tone }> = {
  AVALIDER: { label: "À valider", tone: "warn" },
  ATRAITER: { label: "Validé", tone: "ok" },
  REJETEE: { label: "Rejeté", tone: "danger" },
  ENCOURS: { label: "En cours", tone: "info" },
  SUCCES: { label: "Succès", tone: "done" },
  ERREUR: { label: "Erreur", tone: "err" },
}

export const COHORTE_STATUTS: Record<string, { label: string; tone: Tone }> = {
  AVALIDER: { label: "À valider", tone: "warn" },
  ENCOURS: { label: "En cours", tone: "info" },
  SUCCES: { label: "Traitée", tone: "done" },
}

/** Families of reviewable type_action (stored values: beware SOURCE_SUPRESSION). */
export const TYPE_ACTION_FAMILIES = [
  {
    value: "SOURCE",
    label: "Source",
    types: {
      SOURCE_AJOUT: "Ajout",
      SOURCE_MODIFICATION: "Modification",
      SOURCE_SUPRESSION: "Suppression",
    },
  },
  {
    value: "ENRICH",
    label: "Enrichissement",
    types: {
      ENRICH_ACTEURS_CLOSED: "Acteurs fermés",
      ENRICH_ACTEURS_RGPD: "Anonymisation RGPD",
      ENRICH_ACTEURS_VILLES_TYPO: "Villes typographiques",
      ENRICH_ACTEURS_VILLES_NEW: "Villes nouvelles",
      ENRICH_ACTEURS_CP_TYPO: "Codes postaux non conformes",
      ENRICH_REVISION_ACTEURS_CP_TYPO: "Codes postaux non conformes (corrections)",
      ENRICH_ACTEURS_SIRET: "SIRET depuis le SIREN",
      ENRICH_ACTEURS_SIREN: "SIREN depuis le SIRET",
      ENRICH_ACTEURS_LIEN_SUCCESSION: "Lien de succession",
    },
  },
] as const satisfies readonly {
  value: string
  label: string
  types: Record<string, string>
}[]

export const TYPE_ACTIONS: Record<string, string> = Object.assign(
  {},
  ...TYPE_ACTION_FAMILIES.map((family) => family.types),
)

/** type_action sent to the API for a choice of the type selector: a family
 * (all its types), a single type, or nothing (every type). */
export function typeActionsOf(choice: string | undefined): string[] | undefined {
  if (!choice) {
    return undefined
  }
  const family = TYPE_ACTION_FAMILIES.find((item) => item.value === choice)
  return family ? Object.keys(family.types) : [choice]
}

export const LOG_LEVEL_ORDER = ["ERROR", "WARNING", "INFO"] as const

export type LogLevel = (typeof LOG_LEVEL_ORDER)[number]

export const LOG_LEVELS: Record<
  LogLevel,
  { label: string; plural: string; tone: Tone; icon: string }
> = {
  ERROR: { label: "erreur", plural: "erreurs", tone: "danger", icon: "error-warning" },
  WARNING: {
    label: "avertissement",
    plural: "avertissements",
    tone: "warn",
    icon: "alert",
  },
  INFO: { label: "info", plural: "infos", tone: "info", icon: "information" },
}

/** Most severe level present, or null when there is no log. */
export function worstLogLevel(counts: Record<LogLevel, number>): LogLevel | null {
  return LOG_LEVEL_ORDER.find((level) => counts[level] > 0) ?? null
}
