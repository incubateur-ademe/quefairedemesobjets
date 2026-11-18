import { STATUT_ORDER, STATUTS, type Statut } from "../../domain/statuts"

export type StatutCounts = Record<Statut, number>

export const totalOf = (counts: StatutCounts) =>
  STATUT_ORDER.reduce((total, statut) => total + counts[statut], 0)

/** Progress bar stacked by statut. */
export function StackBar({ counts }: { counts: StatutCounts }) {
  const total = totalOf(counts)
  const title = STATUT_ORDER.map((s) => `${STATUTS[s].label} : ${counts[s]}`).join(
    " · ",
  )
  return (
    <div className="stack" title={title} role="img" aria-label={title}>
      {total > 0 &&
        STATUT_ORDER.filter((s) => counts[s]).map((s) => (
          <span
            key={s}
            className={`bg-${STATUTS[s].tone}`}
            style={{ width: `${(counts[s] / total) * 100}%` }}
          />
        ))}
    </div>
  )
}

export function StatutLegend({ counts }: { counts: StatutCounts }) {
  return (
    <div className="legend">
      {STATUT_ORDER.filter((s) => counts[s]).map((s) => (
        <span key={s} className={`c-${STATUTS[s].tone}`} title={STATUTS[s].label}>
          {counts[s]}
        </span>
      ))}
      <span className="faint">/ {totalOf(counts)}</span>
    </div>
  )
}
