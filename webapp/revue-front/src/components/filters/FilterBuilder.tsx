import { useMemo, useState, type ReactNode } from "react"

import type { FilterField } from "../../api/types"
import {
  appendNode,
  emptyFilter,
  isGroup,
  MAX_DEPTH,
  needsValue,
  newCondition,
  operatorLabel,
  removeNode,
  toApiFilter,
  toDraftFilter,
  updateNode,
  type Condition,
  type FilterGroup,
  type Operator,
} from "../../domain/filterModel"
import { WaButton, WaInput, WaOption, WaSelect } from "../../wa"

const FAMILLE_LABELS: Record<string, string> = {
  cohorte: "Cohorte",
  groupe: "Groupe et acteur",
  ligne: "Ligne de suggestion",
}

type Props = {
  fields: FilterField[]
  value: FilterGroup
  onApply: (filter: FilterGroup) => void
  hint?: ReactNode
}

/** Structured filter builder: conditions combined with ET / OU, nested groups.
 * Edits a local draft, sent to the URL (and the API) on « Appliquer ». */
export function FilterBuilder({ fields, value, onApply, hint }: Props) {
  const fieldsByKey = useMemo(
    () => new Map(fields.map((field) => [field.key, field])),
    [fields],
  )
  const [draft, setDraft] = useState(() => toDraftFilter(value, fieldsByKey))
  const apply = (filter: FilterGroup) => onApply(toApiFilter(filter, fieldsByKey))

  return (
    <form
      className="fb"
      onSubmit={(event) => {
        event.preventDefault()
        apply(draft)
      }}
    >
      <GroupEditor
        group={draft}
        path={[]}
        fields={fields}
        fieldsByKey={fieldsByKey}
        onChange={setDraft}
      />
      {hint && <div className="hint">{hint}</div>}
      <div className="row">
        <WaButton type="submit" size="small" variant="brand">
          Appliquer
        </WaButton>
        <WaButton
          size="small"
          appearance="plain"
          onClick={() => {
            setDraft(emptyFilter())
            apply(emptyFilter())
          }}
        >
          Tout effacer
        </WaButton>
      </div>
    </form>
  )
}

type EditorProps = {
  path: number[]
  fields: FilterField[]
  fieldsByKey: Map<string, FilterField>
  onChange: (update: (root: FilterGroup) => FilterGroup) => void
}

function GroupEditor({
  group,
  path,
  fields,
  fieldsByKey,
  onChange,
}: EditorProps & { group: FilterGroup }) {
  const depth = path.length
  return (
    <div className={depth ? "grp" : undefined}>
      <div className="row">
        <span className="hint">
          {depth ? "Groupe :" : "Afficher les éléments qui vérifient"}
        </span>
        <div className="seg" role="group" aria-label="Combinaison des conditions">
          {(["and", "or"] as const).map((op) => (
            <button
              key={op}
              type="button"
              aria-pressed={group.op === op}
              onClick={() =>
                onChange((root) => updateNode(root, path, (node) => ({ ...node, op })))
              }
            >
              {op === "and" ? "toutes (ET)" : "au moins une (OU)"}
            </button>
          ))}
        </div>
        <span className="hint">des conditions</span>
        {depth > 0 && (
          <WaButton
            size="small"
            appearance="plain"
            aria-label="Supprimer le groupe"
            onClick={() => onChange((root) => removeNode(root, path))}
          >
            ✕
          </WaButton>
        )}
      </div>
      {group.conditions.map((child, index) =>
        isGroup(child) ? (
          <GroupEditor
            key={index}
            group={child}
            path={[...path, index]}
            fields={fields}
            fieldsByKey={fieldsByKey}
            onChange={onChange}
          />
        ) : (
          <ConditionRow
            key={index}
            condition={child}
            path={[...path, index]}
            fields={fields}
            fieldsByKey={fieldsByKey}
            onChange={onChange}
          />
        ),
      )}
      <div className="row">
        <WaButton
          size="small"
          appearance="outlined"
          disabled={!fields.length}
          onClick={() =>
            onChange((root) => appendNode(root, path, newCondition(fields[0])))
          }
        >
          + Condition
        </WaButton>
        {depth < MAX_DEPTH - 1 && (
          <WaButton
            size="small"
            appearance="plain"
            onClick={() =>
              onChange((root) => appendNode(root, path, { op: "and", conditions: [] }))
            }
          >
            + Groupe de conditions
          </WaButton>
        )}
      </div>
    </div>
  )
}

const inputValue = (event: Event) =>
  (event.target as HTMLInputElement & { value: string | string[] }).value

function ConditionRow({
  condition,
  path,
  fields,
  fieldsByKey,
  onChange,
}: EditorProps & { condition: Condition }) {
  const field = fieldsByKey.get(condition.field)
  const update = (patch: Partial<Condition>) =>
    onChange((root) => updateNode(root, path, (node) => ({ ...node, ...patch })))
  const familles = [...new Set(fields.map((f) => f.famille))]

  return (
    <div className="row">
      <WaSelect
        size="small"
        aria-label="Champ"
        className="fb-field"
        value={condition.field}
        onChange={(event) => {
          const next = fieldsByKey.get(inputValue(event as unknown as Event) as string)
          if (next) {
            update(newCondition(next))
          }
        }}
      >
        {familles.map((famille) => [
          familles.length > 1 && <small key={famille}>{FAMILLE_LABELS[famille]}</small>,
          ...fields
            .filter((f) => f.famille === famille)
            .map((f) => (
              <WaOption key={f.key} value={f.key}>
                {f.label}
              </WaOption>
            )),
        ])}
      </WaSelect>
      <WaSelect
        size="small"
        aria-label="Opérateur"
        className="fb-operator"
        value={condition.operator}
        onChange={(event) =>
          update({
            operator: inputValue(event as unknown as Event) as Operator,
            value: undefined,
          })
        }
      >
        {(field?.operateurs ?? []).map((operator) => (
          <WaOption key={operator} value={operator}>
            {operatorLabel(operator as Operator, field)}
          </WaOption>
        ))}
      </WaSelect>
      {field && needsValue(condition.operator) && (
        <ValueInput
          field={field}
          operator={condition.operator}
          value={condition.value}
          onChange={(value) => update({ value })}
        />
      )}
      <WaButton
        size="small"
        appearance="plain"
        aria-label="Supprimer la condition"
        onClick={() => onChange((root) => removeNode(root, path))}
      >
        ✕
      </WaButton>
    </div>
  )
}

function ValueInput({
  field,
  operator,
  value,
  onChange,
}: {
  field: FilterField
  operator: Operator
  value: unknown
  onChange: (value: unknown) => void
}) {
  const type = field.type === "number" || field.type === "user" ? "number" : field.type
  if (operator === "between") {
    const bounds = Array.isArray(value) ? value : ["", ""]
    return (
      <>
        {[0, 1].map((i) => (
          <WaInput
            key={i}
            size="small"
            className="fb-value narrow"
            type={type === "date" ? "date" : "number"}
            aria-label={i ? "Borne haute" : "Borne basse"}
            value={String(bounds[i] ?? "")}
            onInput={(event) => {
              const next = [...bounds]
              next[i] = inputValue(event as unknown as Event)
              onChange(next)
            }}
          />
        ))}
      </>
    )
  }
  if (field.type === "bool" || field.type === "choice") {
    const choices =
      field.type === "bool"
        ? [
            { value: "true", label: "oui" },
            { value: "false", label: "non" },
          ]
        : (field.choix ?? [])
    const multiple = operator === "in"
    return (
      <WaSelect
        size="small"
        className="fb-value"
        aria-label="Valeur"
        multiple={multiple}
        value={
          (multiple ? (Array.isArray(value) ? value : []) : (value ?? "")) as string
        }
        onChange={(event) => onChange(inputValue(event as unknown as Event))}
      >
        {choices.map((choice) => (
          <WaOption key={choice.value} value={choice.value}>
            {choice.label}
          </WaOption>
        ))}
      </WaSelect>
    )
  }
  return (
    <WaInput
      size="small"
      className="fb-value"
      type={
        type === "date"
          ? "date"
          : type === "number" && operator !== "in"
            ? "number"
            : "text"
      }
      aria-label="Valeur"
      placeholder={operator === "in" ? "valeurs séparées par des virgules" : "valeur"}
      value={String(value ?? "")}
      onInput={(event) => onChange(inputValue(event as unknown as Event))}
    />
  )
}
