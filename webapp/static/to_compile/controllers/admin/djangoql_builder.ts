// Pure DjangoQL query generation for the « vue par acteurs » block builder.
// Kept side-effect-free so it can be unit-tested in isolation.

export type FieldType = "text" | "number" | "bool"

export interface QlField {
  name: string
  label: string
  type: FieldType
}

export interface QlOperator {
  // UI value, also used as data-attribute
  value: string
  label: string
  // applicable field types
  types: FieldType[]
  // whether a value input is shown
  needsValue: boolean
}

// The fields exposed to the builder. Mirrors what SuggestionGroupeQLSchema
// understands (model fields forced to text + the custom annotated fields).
export const QL_FIELDS: QlField[] = [
  { name: "id", label: "Identifiant (id)", type: "number" },
  { name: "statut", label: "Statut", type: "text" },
  { name: "contexte", label: "Contexte", type: "text" },
  { name: "metadata", label: "Métadonnées", type: "text" },
  { name: "acteur_id", label: "Identifiant acteur", type: "text" },
  {
    name: "suggestion_unitaires_count",
    label: "Nombre de suggestions",
    type: "number",
  },
  { name: "has_parent", label: "A un parent", type: "bool" },
  { name: "has_correction", label: "A une correction", type: "bool" },
  {
    name: "has_suggestion_unitaire_with_champ",
    label: "Contient une suggestion sur le champ",
    type: "text",
  },
]

export const QL_OPERATORS: QlOperator[] = [
  { value: "=", label: "=", types: ["text", "number", "bool"], needsValue: true },
  { value: "!=", label: "≠", types: ["text", "number", "bool"], needsValue: true },
  { value: "~", label: "contient", types: ["text"], needsValue: true },
  // DjangoQL has no native "startswith"; we approximate it with `~` (contains)
  // and document the limitation in the UI hint.
  { value: "startswith", label: "commence par", types: ["text"], needsValue: true },
  { value: ">", label: ">", types: ["number"], needsValue: true },
  { value: "<", label: "<", types: ["number"], needsValue: true },
  {
    value: "in",
    label: "parmi (séparés par des virgules)",
    types: ["text", "number"],
    needsValue: true,
  },
]

export interface QlRow {
  field: string
  operator: string
  value: string
}

export type QlCombinator = "and" | "or"

export function fieldByName(name: string): QlField | undefined {
  return QL_FIELDS.find((field) => field.name === name)
}

export function operatorsForField(name: string): QlOperator[] {
  const field = fieldByName(name)
  if (!field) {
    return QL_OPERATORS
  }
  return QL_OPERATORS.filter((operator) => operator.types.includes(field.type))
}

export function blankRow(): QlRow {
  return { field: QL_FIELDS[0].name, operator: "=", value: "" }
}

function quote(value: string): string {
  // DjangoQL string literals use double quotes with backslash escaping.
  return `"${value.replace(/\\/g, "\\\\").replace(/"/g, '\\"')}"`
}

function literalForType(type: FieldType, raw: string): string {
  const value = raw.trim()
  if (type === "bool") {
    return value === "true" || value === "True" || value === "1" ? "True" : "False"
  }
  if (type === "number" && value !== "" && !Number.isNaN(Number(value))) {
    return value
  }
  return quote(value)
}

/** Render one row to a DjangoQL clause, or null when it is incomplete. */
export function rowToClause(row: QlRow): string | null {
  const field = fieldByName(row.field)
  if (!field) {
    return null
  }
  const operator = QL_OPERATORS.find((candidate) => candidate.value === row.operator)
  if (!operator || !operator.types.includes(field.type)) {
    return null
  }
  const raw = row.value.trim()
  if (operator.needsValue && raw === "" && field.type !== "bool") {
    return null
  }

  switch (operator.value) {
    case "startswith":
      // approximation: DjangoQL lacks startswith → use contains (~)
      return `${field.name} ~ ${literalForType(field.type, raw)}`
    case "in": {
      const items = raw
        .split(",")
        .map((part) => part.trim())
        .filter((part) => part !== "")
        .map((part) => literalForType(field.type, part))
      if (!items.length) {
        return null
      }
      return `${field.name} in (${items.join(", ")})`
    }
    case "=":
    case "!=":
    case "~":
    case ">":
    case "<":
      return `${field.name} ${operator.value} ${literalForType(field.type, raw)}`
    default:
      return null
  }
}

/** Combine the builder rows into a single DjangoQL query string. */
export function buildDjangoQL(rows: QlRow[], combinator: QlCombinator): string {
  const clauses = rows
    .map(rowToClause)
    .filter((clause): clause is string => clause !== null)
  if (!clauses.length) {
    return ""
  }
  const joiner = combinator === "and" ? " and " : " or "
  return clauses.join(joiner)
}
