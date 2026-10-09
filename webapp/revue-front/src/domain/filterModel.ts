/** Structured filter shared with the API:
 *   { op: "and" | "or", conditions: [{ field, operator, value } | group] }
 * The builder edits a « draft » (raw input strings), converted to API values by
 * `toApiFilter`, which drops incomplete conditions. */
import type { FilterField } from "../api/types"

export type Operator =
  | "eq"
  | "neq"
  | "icontains"
  | "startswith"
  | "in"
  | "is_empty"
  | "is_not_empty"
  | "gt"
  | "lt"
  | "between"

export type Condition = { field: string; operator: Operator; value?: unknown }
export type FilterGroup = { op: "and" | "or"; conditions: FilterNode[] }
export type FilterNode = Condition | FilterGroup

export const MAX_DEPTH = 3

export const emptyFilter = (): FilterGroup => ({ op: "and", conditions: [] })

export const isGroup = (node: FilterNode): node is FilterGroup => "conditions" in node

export const OPERATOR_LABELS: Record<Operator, string> = {
  eq: "est égal à",
  neq: "est différent de",
  icontains: "contient",
  startswith: "commence par",
  in: "parmi",
  is_empty: "est vide",
  is_not_empty: "n’est pas vide",
  gt: "supérieur à",
  lt: "inférieur à",
  between: "entre",
}

const DATE_OPERATOR_LABELS: Partial<Record<Operator, string>> = {
  eq: "le",
  gt: "après le",
  lt: "avant le",
}

export function operatorLabel(operator: Operator, field?: FilterField) {
  return (
    (field?.type === "date" && DATE_OPERATOR_LABELS[operator]) ||
    OPERATOR_LABELS[operator]
  )
}

export const needsValue = (operator: Operator) =>
  operator !== "is_empty" && operator !== "is_not_empty"

export function countConditions(node: FilterNode): number {
  return isGroup(node)
    ? node.conditions.reduce((total, child) => total + countConditions(child), 0)
    : 1
}

/** Reads the `filtre` search param; an invalid value is ignored. */
export function parseFilterParam(raw: string | undefined): FilterGroup {
  if (!raw) {
    return emptyFilter()
  }
  try {
    const parsed = JSON.parse(raw)
    return isValidGroup(parsed) ? parsed : emptyFilter()
  } catch {
    return emptyFilter()
  }
}

function isValidGroup(node: unknown, depth = 1): node is FilterGroup {
  if (typeof node !== "object" || node === null || depth > MAX_DEPTH) {
    return false
  }
  const group = node as FilterGroup
  return (
    (group.op === "and" || group.op === "or") &&
    Array.isArray(group.conditions) &&
    group.conditions.every((child) =>
      typeof child === "object" && child !== null && "conditions" in child
        ? isValidGroup(child, depth + 1)
        : typeof (child as Condition)?.field === "string" &&
          typeof (child as Condition)?.operator === "string",
    )
  )
}

export function serializeFilter(filter: FilterGroup): string | undefined {
  return countConditions(filter) ? JSON.stringify(filter) : undefined
}

// --- Draft <-> API values ---

/** API value → raw value edited in the builder inputs. */
export function toDraftValue(
  value: unknown,
  field: FilterField | undefined,
  operator: Operator,
) {
  if (value === undefined || value === null) {
    return undefined
  }
  if (operator === "between" && Array.isArray(value)) {
    return value.map(String)
  }
  if (operator === "in" && Array.isArray(value) && field?.type !== "choice") {
    return value.join(", ")
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value)
  }
  return value
}

function parseScalar(raw: unknown, field: FilterField): unknown {
  if (typeof raw !== "string" || raw.trim() === "") {
    return undefined
  }
  const text = raw.trim()
  switch (field.type) {
    case "number":
    case "user": {
      const parsed = Number(text)
      return Number.isFinite(parsed) ? parsed : undefined
    }
    case "bool":
      return text === "true" ? true : text === "false" ? false : undefined
    default:
      return text
  }
}

/** Raw value → API value, or undefined when the condition is incomplete. */
export function toApiValue(
  raw: unknown,
  field: FilterField,
  operator: Operator,
): unknown {
  if (!needsValue(operator)) {
    return null
  }
  if (operator === "between") {
    if (!Array.isArray(raw) || raw.length !== 2) {
      return undefined
    }
    const bounds = raw.map((item) => parseScalar(item, field))
    return bounds.every((bound) => bound !== undefined) ? bounds : undefined
  }
  if (operator === "in") {
    const items = Array.isArray(raw)
      ? raw
      : typeof raw === "string"
        ? raw.split(",")
        : []
    const values = items
      .map((item) => parseScalar(item, field))
      .filter((item) => item !== undefined)
    return values.length ? values : undefined
  }
  return parseScalar(raw, field)
}

export function toDraftFilter(
  filter: FilterGroup,
  fields: Map<string, FilterField>,
): FilterGroup {
  return {
    op: filter.op,
    conditions: filter.conditions.map((child) =>
      isGroup(child)
        ? toDraftFilter(child, fields)
        : {
            ...child,
            value: toDraftValue(child.value, fields.get(child.field), child.operator),
          },
    ),
  }
}

export function toApiFilter(
  draft: FilterGroup,
  fields: Map<string, FilterField>,
): FilterGroup {
  const conditions: FilterNode[] = []
  for (const child of draft.conditions) {
    if (isGroup(child)) {
      const group = toApiFilter(child, fields)
      if (group.conditions.length) {
        conditions.push(group)
      }
      continue
    }
    const field = fields.get(child.field)
    if (!field) {
      continue
    }
    const value = toApiValue(child.value, field, child.operator)
    if (value !== undefined) {
      conditions.push({ field: child.field, operator: child.operator, value })
    }
  }
  return { op: draft.op, conditions }
}

// --- Tree edition (path = indexes from the root group) ---

export function updateNode(
  group: FilterGroup,
  path: number[],
  update: (node: FilterNode) => FilterNode,
): FilterGroup {
  if (!path.length) {
    return update(group) as FilterGroup
  }
  const [index, ...rest] = path
  return {
    ...group,
    conditions: group.conditions.map((child, i) =>
      i !== index
        ? child
        : rest.length
          ? updateNode(child as FilterGroup, rest, update)
          : update(child),
    ),
  }
}

export function removeNode(group: FilterGroup, path: number[]): FilterGroup {
  const parentPath = path.slice(0, -1)
  const index = path[path.length - 1]
  return updateNode(group, parentPath, (parent) => ({
    ...(parent as FilterGroup),
    conditions: (parent as FilterGroup).conditions.filter((_, i) => i !== index),
  }))
}

export function appendNode(
  group: FilterGroup,
  path: number[],
  node: FilterNode,
): FilterGroup {
  return updateNode(group, path, (parent) => ({
    ...(parent as FilterGroup),
    conditions: [...(parent as FilterGroup).conditions, node],
  }))
}

export function newCondition(field: FilterField): Condition {
  return { field: field.key, operator: field.operateurs[0] as Operator }
}
