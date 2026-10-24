import { useState } from "react"

import type { MassAction, MassCounts } from "../../api/masse"
import type { Policy, Vue } from "../../api/types"
import { plural } from "../../domain/format"
import { WaButton, WaDialog, WaSpinner } from "../../wa"

/** Confirmation required: a refusal, a « tout le filtre » selection, or more than
 * CONFIRM_ABOVE elements. */
export const CONFIRM_ABOVE = 50

const UNITS: Record<Vue, [string, string, string]> = {
  groupes: ["groupe", "groupes", "sélectionné"],
  lignes: ["ligne", "lignes", "sélectionnée"],
}

const LABELS: Record<MassAction, string> = {
  validate: "Valider",
  reject: "Refuser…",
  resubmit: "Remettre à valider",
  report_correction: "▶ Reporter vers la correction",
  report_parent: "⏩ Reporter vers le parent",
}

const VERBS: Record<MassAction, string> = {
  validate: "Valider",
  reject: "Refuser",
  resubmit: "Remettre à valider",
  report_correction: "Reporter vers la correction les suggestions de",
  report_parent: "Reporter vers le parent les suggestions de",
}

export function needsConfirmation(
  action: MassAction,
  count: number,
  filterMode: boolean,
) {
  return action === "reject" || filterMode || count > CONFIRM_ABOVE
}

/** Selection bar and mass actions; each button gives the number of elements it
 * really changes (disabled at 0). */
export function MassBar({
  vue,
  policy,
  count,
  total,
  filterMode,
  canSelectFilter,
  counts,
  loadingCounts,
  running,
  job,
  onSelectFilter,
  onClear,
  onRun,
}: {
  vue: Vue
  policy: Policy
  count: number
  total: number
  filterMode: boolean
  canSelectFilter: boolean
  counts: MassCounts | undefined
  loadingCounts: boolean
  running: boolean
  job: { total: number } | null
  onSelectFilter: () => void
  onClear: () => void
  onRun: (action: MassAction) => void
}) {
  const [singular, pluralForm, selected] = UNITS[vue]
  const [confirming, setConfirming] = useState<MassAction | null>(null)
  const actions: MassAction[] = [
    "validate",
    ...(vue === "groupes" && policy.can_reject_group ? (["reject"] as const) : []),
    "resubmit",
    ...(policy.editable_models.includes("RevisionActeur")
      ? (["report_correction"] as const)
      : []),
    ...(policy.shows_parent ? (["report_parent"] as const) : []),
  ]
  const start = (action: MassAction) => {
    if (needsConfirmation(action, counts?.[action] ?? 0, filterMode)) {
      setConfirming(action)
    } else {
      onRun(action)
    }
  }
  return (
    <div className="massbar" role="region" aria-label="Sélection">
      <span>
        {filterMode ? (
          <>
            Les <b>{plural(count, singular, pluralForm)}</b> répondant au filtre sont{" "}
            {selected}s
          </>
        ) : (
          <>
            <b>{plural(count, singular, pluralForm)}</b>{" "}
            {`${selected}${count > 1 ? "s" : ""}`}
          </>
        )}
      </span>
      {canSelectFilter && (
        <button type="button" className="lk" onClick={onSelectFilter}>
          Sélectionner les {plural(total, singular, pluralForm)} répondant au filtre
        </button>
      )}
      <button type="button" className="lk" onClick={onClear}>
        Effacer la sélection
      </button>
      <span className="spacer" />
      {(loadingCounts || running) && <WaSpinner />}
      {job && (
        <span className="muted">Report en cours ({plural(job.total, "élément")})…</span>
      )}
      {actions.map((action) => {
        const n = counts?.[action] ?? 0
        return (
          <WaButton
            key={action}
            size="small"
            variant={
              action === "validate"
                ? "success"
                : action === "reject"
                  ? "danger"
                  : "neutral"
            }
            appearance={action === "validate" ? "accent" : "outlined"}
            disabled={!n || running}
            onClick={() => start(action)}
          >
            {LABELS[action]} <span className="mono">{n}</span>
          </WaButton>
        )
      })}
      <WaDialog
        open={confirming !== null}
        label="Confirmer l’action de masse"
        className="confirm-dialog"
        onWaAfterHide={(event) => {
          if (event.target === event.currentTarget) {
            setConfirming(null)
          }
        }}
      >
        {confirming && (
          <p>
            {VERBS[confirming]}{" "}
            <b>{plural(counts?.[confirming] ?? 0, singular, pluralForm)}</b>
            {filterMode ? " (toutes les pages du filtre)" : ""} ?
          </p>
        )}
        <WaButton slot="footer" appearance="plain" onClick={() => setConfirming(null)}>
          Annuler
        </WaButton>
        <WaButton
          slot="footer"
          variant={confirming === "reject" ? "danger" : "brand"}
          onClick={() => {
            const action = confirming
            setConfirming(null)
            if (action) {
              onRun(action)
            }
          }}
        >
          Confirmer
        </WaButton>
      </WaDialog>
    </div>
  )
}
