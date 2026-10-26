import type { ReactNode } from "react"

import { formatDateTime } from "../../domain/format"
import { COHORTE_STATUTS, STATUTS, type Statut, type Tone } from "../../domain/statuts"

export function Pill({
  tone,
  title,
  children,
}: {
  tone: Tone
  title?: string
  children: ReactNode
}) {
  return (
    <span className={`pill p-${tone}`} title={title}>
      <span className="dot" />
      {children}
    </span>
  )
}

/** Statut of a groupe or a ligne; its decision (who, when) in title. */
export function StatutPill({
  statut,
  decision,
}: {
  statut: string
  decision?: { par: { username: string } | null; le: string | null }
}) {
  const meta = STATUTS[statut as Statut]
  const title =
    decision?.par && decision.le
      ? `${decision.par.username} · ${formatDateTime(decision.le)}`
      : undefined
  return meta ? (
    <Pill tone={meta.tone} title={title}>
      {meta.label}
    </Pill>
  ) : (
    <span title={title}>{statut}</span>
  )
}

export function CohorteStatutPill({ statut }: { statut: string }) {
  const meta = COHORTE_STATUTS[statut]
  return meta ? <Pill tone={meta.tone}>{meta.label}</Pill> : <span>{statut}</span>
}

/** Statut of a cohorte as a colored dot, its label in title. */
export function CohorteStatutDot({ statut }: { statut: string }) {
  const meta = COHORTE_STATUTS[statut]
  const label = meta?.label ?? statut
  return (
    <span
      className={`sdot p-${meta?.tone ?? "done"}`}
      role="img"
      aria-label={`Statut : ${label}`}
      title={label}
    />
  )
}
