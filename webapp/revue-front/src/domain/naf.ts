/** Labels of the NAF codes (nomenclature of the INSEE, rev. 2), the public API
 * « Recherche d'entreprises » only giving the code. */
import codes from "@socialgouv/codes-naf/index.json"

const LABELS = new Map(
  (codes as { id: string; label: string }[]).map((c) => [c.id, c.label]),
)

export function nafLabel(code: string | null | undefined): string | undefined {
  return code ? LABELS.get(code) : undefined
}
