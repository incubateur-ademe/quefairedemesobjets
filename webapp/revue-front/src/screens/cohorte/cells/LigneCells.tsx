import { useEffect, useRef, useState } from "react"

import { ApiError } from "../../../api/client"
import type { GroupeActions } from "../../../api/mutations"
import type { Groupe, Ligne, Modele, Policy } from "../../../api/types"
import { StatutPill } from "../../../components/common/Pill"
import { ChampsValues, DiffValue } from "../../../components/common/Value"
import { formatDateTime } from "../../../domain/format"
import { WaButton, WaInput } from "../../../wa"

const TARGETS: Record<
  Modele,
  { column: "correction" | "parent"; label: string; icon: string }
> = {
  RevisionActeur: { column: "correction", label: "vers la correction", icon: "▶" },
  ParentRevisionActeur: { column: "parent", label: "vers le parent", icon: "⏩" },
}

const capacity = (modele: Modele, verb: "corriger" | "reporter" | "supprimer") =>
  `${verb}_${TARGETS[modele].column}` as keyof Ligne["capacites"]

export function ChampsCell({ ligne }: { ligne: Ligne }) {
  return (
    <span className="champs">
      {ligne.champs.map((champ) => (
        <span key={champ} className="champ">
          {champ}
        </span>
      ))}
    </span>
  )
}

/** Acteur importé: suggestion of the source, never corrected. */
export function ActeurCell({ ligne }: { ligne: Ligne }) {
  const { actuel, propose } = ligne.acteur
  return (
    <ChampsValues
      champs={ligne.champs}
      render={(champ) => (
        <DiffValue actuel={actuel?.[champ]} propose={propose?.[champ]} empty="—" />
      )}
    />
  )
}

export function ReportButton({
  groupe,
  ligne,
  modele,
  actions,
}: {
  groupe: Groupe
  ligne: Ligne
  modele: Modele
  actions: GroupeActions
}) {
  if (modele === "ParentRevisionActeur" && !ligne.parent) {
    return null
  }
  if (!ligne.capacites[capacity(modele, "reporter")]) {
    return <span className="repoff">·</span>
  }
  const target = TARGETS[modele]
  return (
    <button
      type="button"
      className="rep"
      title={`Reporter la suggestion de l’acteur ${target.label}`}
      aria-label={`Reporter ${ligne.champs.join(", ")} ${target.label}`}
      onClick={(event) => {
        event.stopPropagation()
        actions.report(groupe, modele, [ligne.key]).catch(() => {})
      }}
    >
      {target.icon}
    </button>
  )
}

/** Correction (RevisionActeur) or Parent (ParentRevisionActeur): current value
 * and proposition, editable (✎) and removable (✕). */
export function TargetCell({
  groupe,
  ligne,
  modele,
  actions,
}: {
  groupe: Groupe
  ligne: Ligne
  modele: Modele
  actions: GroupeActions
}) {
  const [editing, setEditing] = useState(false)
  const cell = ligne[TARGETS[modele].column]
  if (!cell) {
    return <span className="inherit">pas de parent</span>
  }
  if (editing) {
    return (
      <EditForm
        ligne={ligne}
        initial={cell.propose ?? cell.actuel ?? ligne.acteur.propose ?? {}}
        onCancel={() => setEditing(false)}
        onSave={async (valeurs) => {
          await actions.upsertProposition(groupe, ligne, modele, valeurs)
          setEditing(false)
        }}
      />
    )
  }
  const empty =
    modele === "RevisionActeur"
      ? cell.actuel
        ? "hérite de l’acteur"
        : "pas de correction"
      : "hérite des enfants"
  const canEdit = ligne.capacites[capacity(modele, "corriger")]
  const canDelete = ligne.capacites[capacity(modele, "supprimer")]
  return (
    <div className="sugcell">
      <ChampsValues
        champs={ligne.champs}
        render={(champ) => (
          <DiffValue
            actuel={cell.actuel?.[champ]}
            propose={cell.propose?.[champ]}
            empty={empty}
          />
        )}
      />
      {(canEdit || canDelete) && (
        <span className="sugbtns">
          {canEdit && (
            <button
              type="button"
              className="editbtn"
              title={cell.propose ? "Corriger la proposition" : "Proposer une valeur"}
              onClick={(event) => {
                event.stopPropagation()
                setEditing(true)
              }}
            >
              ✎
            </button>
          )}
          {canDelete && (
            <button
              type="button"
              className="delbtn"
              title={`Supprimer la proposition de la colonne ${modele === "RevisionActeur" ? "Correction" : "Parent"}`}
              onClick={(event) => {
                event.stopPropagation()
                actions.deleteProposition(groupe, ligne, modele).catch(() => {})
              }}
            >
              ✕
            </button>
          )}
        </span>
      )}
    </div>
  )
}

function EditForm({
  ligne,
  initial,
  onSave,
  onCancel,
}: {
  ligne: Ligne
  initial: Record<string, string>
  onSave: (valeurs: Record<string, string>) => Promise<void>
  onCancel: () => void
}) {
  const [draft, setDraft] = useState(() =>
    Object.fromEntries(ligne.champs.map((champ) => [champ, initial[champ] ?? ""])),
  )
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const firstInput = useRef<HTMLElement>(null)
  useEffect(() => {
    // Lit renders the inner <input> asynchronously: focus once it is rendered
    const input = firstInput.current as
      (HTMLElement & { updateComplete?: Promise<unknown> }) | null
    Promise.resolve(input?.updateComplete).then(
      () => input?.isConnected && input.focus(),
    )
  }, [])
  const save = () =>
    onSave(draft).catch((error) => {
      if (error instanceof ApiError && error.body.errors) {
        setErrors(error.body.errors)
      }
    })
  return (
    <form
      className="edit"
      onClick={(event) => event.stopPropagation()}
      onKeyDown={(event) => {
        event.stopPropagation()
        if (event.key === "Escape") {
          onCancel()
        }
      }}
      onSubmit={(event) => {
        event.preventDefault()
        save()
      }}
    >
      {ligne.champs.map((champ, index) => {
        const fieldErrors =
          errors[champ] ?? (index === 0 ? (errors.error ?? errors.__all__) : undefined)
        return (
          <div key={champ} className="edit__field">
            <WaInput
              size="small"
              label={champ}
              value={draft[champ]}
              ref={index === 0 ? (firstInput as never) : undefined}
              className={fieldErrors ? "bad" : undefined}
              onInput={(event) =>
                setDraft((current) => ({
                  ...current,
                  [champ]: (event.target as HTMLInputElement).value,
                }))
              }
            />
            {fieldErrors && <span className="ferr">{fieldErrors.join(" ")}</span>}
          </div>
        )
      })}
      <div className="eacts">
        <WaButton size="small" variant="brand" type="submit">
          Enregistrer <kbd>⏎</kbd>
        </WaButton>
        <WaButton size="small" appearance="plain" onClick={onCancel}>
          Annuler <kbd>Échap</kbd>
        </WaButton>
      </div>
    </form>
  )
}

export function Decided({
  par,
  le,
}: {
  par: { username: string } | null
  le: string | null
}) {
  return par && le ? (
    <div className="decided">
      {par.username} · {formatDateTime(le)}
    </div>
  ) : null
}

const PROCESSING = ["ENCOURS", "SUCCES", "ERREUR"]

export function StatutCell({ ligne }: { ligne: Ligne }) {
  return (
    <>
      <StatutPill statut={ligne.statut} />
      <Decided par={ligne.decision_par} le={ligne.decision_le} />
    </>
  )
}

export function LigneActionCell({
  groupe,
  ligne,
  actions,
}: {
  groupe: Groupe
  ligne: Ligne
  actions: GroupeActions
}) {
  const run = (action: "validate" | "resubmit") => (event: React.MouseEvent) => {
    event.stopPropagation()
    actions.decideLignes(groupe, [ligne.key], action).catch(() => {})
  }
  if (ligne.capacites.valider) {
    return (
      <WaButton size="small" variant="success" onClick={run("validate")}>
        Valider la ligne
      </WaButton>
    )
  }
  if (ligne.capacites.remettre_groupe_a_valider) {
    return (
      <WaButton
        size="small"
        appearance="outlined"
        title="Le refus porte sur le groupe : tout le groupe revient à valider"
        onClick={run("resubmit")}
      >
        Remettre le groupe à valider
      </WaButton>
    )
  }
  if (ligne.capacites.remettre_a_valider) {
    return (
      <WaButton size="small" appearance="outlined" onClick={run("resubmit")}>
        Remettre à valider
      </WaButton>
    )
  }
  if (PROCESSING.includes(groupe.statut)) {
    return <span className="lock">lecture seule</span>
  }
  return null
}

export type LigneRowProps = {
  groupe: Groupe
  ligne: Ligne
  policy: Policy
  actions: GroupeActions
}
