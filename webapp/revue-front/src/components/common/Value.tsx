import {
  DIFF_DELETE,
  DIFF_EQUAL,
  DIFF_INSERT,
  diff_match_patch as DiffMatchPatch,
} from "diff-match-patch"

import { externalLink } from "../../domain/externalLinks"

const dmp = new DiffMatchPatch()

/** Differences between two values, like `diff_display` of the admin. */
export function diffSegments(
  actuel: string,
  propose: string,
): ["equal" | "removed" | "added", string][] {
  const diffs = dmp.diff_main(actuel, propose)
  dmp.diff_cleanupSemantic(diffs)
  const kinds = {
    [DIFF_EQUAL]: "equal",
    [DIFF_DELETE]: "removed",
    [DIFF_INSERT]: "added",
  } as const
  return diffs.map(([op, text]) => [kinds[op as keyof typeof kinds], text])
}

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

/** Current value and proposition: removed parts struck out, added parts
 * highlighted, like `display_diff_values` of the admin. */
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
  if (actuel === propose || (!actuel && propose === "")) {
    return <Value value={propose} />
  }
  return (
    <>
      <span className="val">
        {diffSegments(actuel ?? "", propose).map(([kind, text], index) =>
          kind === "removed" ? (
            <del key={index}>{text}</del>
          ) : kind === "added" ? (
            <ins key={index}>{text}</ins>
          ) : (
            text
          ),
        )}
      </span>
      {propose === "" ? (
        <span className="empty"> vide</span>
      ) : (
        <ExternalLink value={propose} />
      )}
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
