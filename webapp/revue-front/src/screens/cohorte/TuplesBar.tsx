import type { Stats, Vue } from "../../api/types"

/** One chip per tuple of champs, multiple selection. */
export function TuplesBar({
  stats,
  vue,
  selected,
  onChange,
}: {
  stats: Stats | undefined
  vue: Vue
  selected: string[]
  onChange: (tuples: string[]) => void
}) {
  const toggle = (key: string) =>
    onChange(
      selected.includes(key)
        ? selected.filter((item) => item !== key)
        : [...selected, key],
    )
  return (
    <div className="tuplebar">
      <span className="tlabel">Tuples de champs</span>
      {stats?.tuples.map(({ champs, count }) => {
        const key = champs.join(",")
        return (
          <button
            key={key}
            type="button"
            className="chip"
            aria-pressed={selected.includes(key)}
            onClick={() => toggle(key)}
          >
            {champs.join(" + ")}
            <span className="n">{count}</span>
          </button>
        )
      })}
      {selected.length > 0 && (
        <button type="button" className="chip chip--ghost" onClick={() => onChange([])}>
          Tous
        </button>
      )}
      <span className="spacer" />
      <span className="muted">
        {vue === "groupes"
          ? "nombre de groupes ayant au moins une ligne sur ce tuple"
          : "nombre de lignes par tuple"}
      </span>
    </div>
  )
}
