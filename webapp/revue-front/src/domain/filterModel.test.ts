import type { FilterField } from "../api/types"
import {
  appendNode,
  countConditions,
  emptyFilter,
  parseFilterParam,
  removeNode,
  serializeFilter,
  toApiFilter,
  toDraftFilter,
  updateNode,
  type FilterGroup,
} from "./filterModel"

const field = (
  key: string,
  type: FilterField["type"],
  operateurs: string[],
): FilterField => ({
  key,
  label: key,
  famille: "cohorte",
  type,
  operateurs,
})

const FIELDS = new Map(
  [
    field("identifiant_action", "text", ["icontains", "in", "is_empty"]),
    field("id", "number", ["eq", "between"]),
    field("type_action", "choice", ["eq", "in"]),
    field("cree_le", "date", ["gt"]),
  ].map((f) => [f.key, f]),
)

describe("URL serialization", () => {
  it("round-trips a filter and drops an empty one", () => {
    const filter: FilterGroup = {
      op: "or",
      conditions: [{ field: "id", operator: "eq", value: 3 }],
    }
    expect(parseFilterParam(serializeFilter(filter))).toEqual(filter)
    expect(serializeFilter(emptyFilter())).toBeUndefined()
  })

  it.each(["{", '{"op":"xor","conditions":[]}', '{"op":"and","conditions":[{}]}'])(
    "ignores an invalid filter: %s",
    (raw) => {
      expect(parseFilterParam(raw)).toEqual(emptyFilter())
    },
  )
})

describe("draft to API values", () => {
  it("converts raw inputs and drops incomplete conditions", () => {
    const draft: FilterGroup = {
      op: "and",
      conditions: [
        { field: "identifiant_action", operator: "in", value: "a, b ,," },
        { field: "id", operator: "between", value: ["1", "10"] },
        { field: "id", operator: "eq", value: "" },
        { field: "type_action", operator: "in", value: ["SOURCE_AJOUT"] },
        { field: "identifiant_action", operator: "is_empty" },
        { field: "inconnu", operator: "eq", value: "x" },
        { op: "or", conditions: [{ field: "cree_le", operator: "gt" }] },
      ],
    }
    expect(toApiFilter(draft, FIELDS)).toEqual({
      op: "and",
      conditions: [
        { field: "identifiant_action", operator: "in", value: ["a", "b"] },
        { field: "id", operator: "between", value: [1, 10] },
        { field: "type_action", operator: "in", value: ["SOURCE_AJOUT"] },
        { field: "identifiant_action", operator: "is_empty", value: null },
      ],
    })
  })

  it("converts API values back to editable drafts", () => {
    const api: FilterGroup = {
      op: "and",
      conditions: [
        { field: "identifiant_action", operator: "in", value: ["a", "b"] },
        { field: "id", operator: "between", value: [1, 10] },
      ],
    }
    expect(toDraftFilter(api, FIELDS).conditions).toEqual([
      { field: "identifiant_action", operator: "in", value: "a, b" },
      { field: "id", operator: "between", value: ["1", "10"] },
    ])
    expect(toApiFilter(toDraftFilter(api, FIELDS), FIELDS)).toEqual(api)
  })
})

describe("tree edition", () => {
  it("adds, updates and removes nodes by path", () => {
    let filter = appendNode(emptyFilter(), [], { op: "or", conditions: [] })
    filter = appendNode(filter, [0], { field: "id", operator: "eq", value: "1" })
    filter = updateNode(filter, [0, 0], (node) => ({ ...node, value: "2" }))
    expect(filter).toEqual({
      op: "and",
      conditions: [
        { op: "or", conditions: [{ field: "id", operator: "eq", value: "2" }] },
      ],
    })
    expect(countConditions(filter)).toBe(1)
    expect(removeNode(filter, [0, 0])).toEqual({
      op: "and",
      conditions: [{ op: "or", conditions: [] }],
    })
  })
})
