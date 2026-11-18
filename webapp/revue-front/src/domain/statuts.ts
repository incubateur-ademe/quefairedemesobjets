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

export const TYPE_ACTIONS: Record<string, string> = {
  SOURCE_AJOUT: "Ajout",
  SOURCE_MODIFICATION: "Modification",
  SOURCE_SUPRESSION: "Suppression",
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
