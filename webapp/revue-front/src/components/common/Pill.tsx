import type { ReactNode } from "react"

import { COHORTE_STATUTS, STATUTS, type Statut, type Tone } from "../../domain/statuts"

export function Pill({ tone, children }: { tone: Tone; children: ReactNode }) {
  return (
    <span className={`pill p-${tone}`}>
      <span className="dot" />
      {children}
    </span>
  )
}

export function StatutPill({ statut }: { statut: string }) {
  const meta = STATUTS[statut as Statut]
  return meta ? <Pill tone={meta.tone}>{meta.label}</Pill> : <span>{statut}</span>
}

export function CohorteStatutPill({ statut }: { statut: string }) {
  const meta = COHORTE_STATUTS[statut]
  return meta ? <Pill tone={meta.tone}>{meta.label}</Pill> : <span>{statut}</span>
}
