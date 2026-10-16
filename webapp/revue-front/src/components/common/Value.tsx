import { externalLink } from "../../domain/externalLinks"

export function ExternalLink({ value }: { value: unknown }) {
  const link = externalLink(value)
  return link ? (
    <a
      className="xl"
      href={link.href}
      title={link.title}
      target="_blank"
      rel="noopener noreferrer"
    >
      {link.label} ↗
    </a>
  ) : null
}

/** A value with its external link (URL, SIRET, SIREN). */
export function Value({
  value,
  className = "",
}: {
  value: string | null | undefined
  className?: string
}) {
  if (value === null || value === undefined || value === "") {
    return <span className="empty">vide</span>
  }
  return (
    <>
      <span className={`val ${className}`}>{value}</span>
      <ExternalLink value={value} />
    </>
  )
}

/** Current value and proposition: old value struck out, new value highlighted,
 * like `display_diff_values` of the admin. */
export function DiffValue({
  actuel,
  propose,
  empty,
}: {
  actuel: string | null | undefined
  propose: string | null | undefined
  /** Shown when there is neither a current value nor a proposition */
  empty: string
}) {
  const hasProposition = propose !== null && propose !== undefined
  if (!hasProposition) {
    return actuel === null || actuel === undefined ? (
      <span className="inherit">{empty}</span>
    ) : actuel === "" ? (
      <span className="inherit">{empty}</span>
    ) : (
      <Value value={actuel} />
    )
  }
  if (actuel === null || actuel === undefined || actuel === "" || actuel === propose) {
    return <Value value={propose} className={actuel === propose ? "" : "chg"} />
  }
  return (
    <>
      <Value value={actuel} className="old" />
      <span className="arrow">→</span>
      <Value value={propose} className="chg" />
    </>
  )
}

/** One or several champs of a ligne. */
export function ChampsValues({
  champs,
  render,
}: {
  champs: string[]
  render: (champ: string) => React.ReactNode
}) {
  if (champs.length === 1) {
    return <div className="dv">{render(champs[0])}</div>
  }
  return (
    <div className="kv">
      {champs.map((champ) => (
        <div key={champ} className="kv__item">
          <span className="k">{champ}</span>
          <span className="dv">{render(champ)}</span>
        </div>
      ))}
    </div>
  )
}
