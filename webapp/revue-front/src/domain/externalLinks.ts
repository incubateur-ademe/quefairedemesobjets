/** External links detected from the format of a value (current or proposed). */
export const ANNUAIRE_ENTREPRISES = "https://annuaire-entreprises.data.gouv.fr"

export type ExternalLink = { href: string; label: string; title: string }

export function externalLink(value: unknown): ExternalLink | null {
  const text = String(value ?? "").trim()
  if (!text) {
    return null
  }
  if (/^https?:\/\/\S+\.\S+$/i.test(text)) {
    return { href: text, label: "voir le site", title: text }
  }
  const digits = text.replace(/\s/g, "")
  if (/^\d{14}$/.test(digits)) {
    return {
      href: `${ANNUAIRE_ENTREPRISES}/etablissement/${digits}`,
      label: "voir dans AE",
      title: `SIRET ${digits} dans l’Annuaire des entreprises`,
    }
  }
  if (/^\d{9}$/.test(digits)) {
    return {
      href: `${ANNUAIRE_ENTREPRISES}/entreprise/${digits}`,
      label: "voir dans AE",
      title: `SIREN ${digits} dans l’Annuaire des entreprises`,
    }
  }
  return null
}
