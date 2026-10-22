import { useEffect, useRef, useState } from "react"

import { ApiError } from "../../../api/client"
import type { GroupeActions } from "../../../api/mutations"
import { useChampsChoix } from "../../../api/queries"
import type { ChampChoix, Groupe, Ligne, Modele, Policy } from "../../../api/types"
import { StatutPill } from "../../../components/common/Pill"
import { ChampsValues, DiffValue } from "../../../components/common/Value"
import { WaButton, WaInput, WaOption, WaSelect } from "../../../wa"

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
  const choix = useChampsChoix().data
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
            <ChampInput
              champ={champ}
              value={draft[champ]}
              choix={choix?.[champ]}
              invalid={Boolean(fieldErrors)}
              inputRef={index === 0 ? firstInput : undefined}
              onChange={(value) =>
                setDraft((current) => ({ ...current, [champ]: value }))
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

/** Codes of a `*_codes` value: a JSON list (quotes ' accepted, as when the
 * suggestion is applied). */
export function parseCodes(value: string): string[] {
  try {
    const codes = JSON.parse(value.replace(/'/g, '"'))
    return Array.isArray(codes) ? codes.map(String) : []
  } catch {
    return value ? [value] : []
  }
}

type Choice = ChampChoix["choix"][number]

/** Choices, plus the selected values missing from them: they stay shown (and
 * selectable) rather than being lost silently. */
function withSelected(choices: Choice[], selected: string[]): Choice[] {
  return [
    ...choices,
    ...selected
      .filter((code) => code && !choices.some((choice) => choice.value === code))
      .map((code) => ({ value: code, label: code })),
  ]
}

type PropositionService = { action: string; sous_categories: string[] }

/** Services of a `proposition_service_codes` value: a JSON list of
 * {action, sous_categories} (quotes ' accepted, as when applied). */
export function parsePropositions(value: string): PropositionService[] {
  try {
    const rows = JSON.parse(value.replace(/'/g, '"'))
    return Array.isArray(rows)
      ? rows.map((row) => ({
          action: String(row?.action ?? ""),
          sous_categories: Array.isArray(row?.sous_categories)
            ? row.sous_categories.map(String)
            : [],
        }))
      : []
  } catch {
    return []
  }
}

const selectValue = (event: unknown) =>
  ((event as Event).target as unknown as { value: string | string[] }).value

/** One row per action (select, each action once) with its sous-catégories
 * (multiple select); rows are added and removed. */
function PropositionsInput({
  champ,
  value,
  choix,
  invalid,
  onChange,
}: {
  champ: string
  value: string
  choix: ChampChoix & { actions: Choice[] }
  invalid: boolean
  onChange: (value: string) => void
}) {
  const rows = parsePropositions(value)
  const set = (next: PropositionService[]) => onChange(JSON.stringify(next))
  const update = (index: number, patch: Partial<PropositionService>) =>
    set(rows.map((row, i) => (i === index ? { ...row, ...patch } : row)))
  return (
    <fieldset className={`services${invalid ? " bad" : ""}`}>
      <legend>{champ}</legend>
      {rows.map((row, index) => {
        const taken = rows.filter((_, i) => i !== index).map((other) => other.action)
        return (
          <div key={index} className="services__row">
            <WaSelect
              size="small"
              aria-label={`Action ${index + 1}`}
              placeholder="Action"
              value={row.action}
              onChange={(event) =>
                update(index, { action: selectValue(event) as string })
              }
            >
              {withSelected(choix.actions, [row.action])
                .filter((action) => !taken.includes(action.value))
                .map((action) => (
                  <WaOption key={action.value} value={action.value}>
                    {action.label}
                  </WaOption>
                ))}
            </WaSelect>
            <WaSelect
              size="small"
              multiple
              aria-label={`Sous-catégories de l’action ${index + 1}`}
              placeholder="Sous-catégories"
              value={row.sous_categories as unknown as string}
              onChange={(event) =>
                update(index, { sous_categories: selectValue(event) as string[] })
              }
            >
              {withSelected(choix.choix, row.sous_categories).map((sousCategorie) => (
                <WaOption key={sousCategorie.value} value={sousCategorie.value}>
                  {sousCategorie.label}
                </WaOption>
              ))}
            </WaSelect>
            <WaButton
              size="small"
              appearance="plain"
              variant="danger"
              title={`Supprimer l’action ${index + 1}`}
              onClick={() => set(rows.filter((_, i) => i !== index))}
            >
              ✕
            </WaButton>
          </div>
        )
      })}
      <WaButton
        size="small"
        appearance="outlined"
        className="services__add"
        disabled={rows.length >= choix.actions.length}
        onClick={() => set([...rows, { action: "", sous_categories: [] }])}
      >
        + Ajouter une action
      </WaButton>
    </fieldset>
  )
}

/** Text input, or select when the field has a list of values (`choix`): several
 * codes are written as a JSON list. */
function ChampInput({
  champ,
  value,
  choix,
  invalid,
  inputRef,
  onChange,
}: {
  champ: string
  value: string
  choix: ChampChoix | undefined
  invalid: boolean
  inputRef?: React.RefObject<HTMLElement | null>
  onChange: (value: string) => void
}) {
  const className = invalid ? "bad" : undefined
  if (choix?.actions) {
    return (
      <PropositionsInput
        champ={champ}
        value={value}
        choix={{ ...choix, actions: choix.actions }}
        invalid={invalid}
        onChange={onChange}
      />
    )
  }
  if (!choix) {
    return (
      <WaInput
        size="small"
        label={champ}
        value={value}
        ref={inputRef as never}
        className={className}
        onInput={(event) => onChange((event.target as HTMLInputElement).value)}
      />
    )
  }
  const selected = choix.multiple ? parseCodes(value) : value ? [value] : []
  const options = withSelected(choix.choix, selected)
  return (
    <WaSelect
      size="small"
      label={champ}
      multiple={choix.multiple}
      value={(choix.multiple ? selected : value) as string}
      placeholder="(vide)"
      ref={inputRef as never}
      className={className}
      onChange={(event) => {
        const next = selectValue(event)
        onChange(Array.isArray(next) ? JSON.stringify(next) : next)
      }}
    >
      {options.map((option) => (
        <WaOption key={option.value} value={option.value}>
          {option.label}
        </WaOption>
      ))}
    </WaSelect>
  )
}

const PROCESSING = ["ENCOURS", "SUCCES", "ERREUR"]

export function StatutCell({ ligne }: { ligne: Ligne }) {
  return (
    <>
      <StatutPill
        statut={ligne.statut}
        decision={{ par: ligne.decision_par, le: ligne.decision_le }}
      />
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
