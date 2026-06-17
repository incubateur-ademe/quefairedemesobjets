import {
  blankRow,
  buildDjangoQL,
  operatorsForField,
  rowToClause,
} from "../controllers/admin/djangoql_builder"

describe("rowToClause", () => {
  it("renders a text equality with quoting", () => {
    expect(rowToClause({ field: "acteur_id", operator: "=", value: "ABC" })).toBe(
      'acteur_id = "ABC"',
    )
  })

  it("escapes quotes and backslashes in string literals", () => {
    expect(rowToClause({ field: "contexte", operator: "~", value: 'a"b\\c' })).toBe(
      'contexte ~ "a\\"b\\\\c"',
    )
  })

  it("maps « contient » to ~", () => {
    expect(rowToClause({ field: "contexte", operator: "~", value: "foo" })).toBe(
      'contexte ~ "foo"',
    )
  })

  it("approximates « commence par » with ~ (no native startswith)", () => {
    expect(
      rowToClause({ field: "contexte", operator: "startswith", value: "foo" }),
    ).toBe('contexte ~ "foo"')
  })

  it("renders numbers without quotes", () => {
    expect(rowToClause({ field: "id", operator: ">", value: "42" })).toBe("id > 42")
  })

  it("renders booleans as True/False", () => {
    expect(rowToClause({ field: "has_parent", operator: "=", value: "true" })).toBe(
      "has_parent = True",
    )
    expect(rowToClause({ field: "has_parent", operator: "=", value: "false" })).toBe(
      "has_parent = False",
    )
  })

  it("renders an in() list", () => {
    expect(
      rowToClause({ field: "statut", operator: "in", value: "AVALIDER, REJETEE" }),
    ).toBe('statut in ("AVALIDER", "REJETEE")')
  })

  it("returns null for an empty value on a text field", () => {
    expect(rowToClause({ field: "acteur_id", operator: "=", value: "  " })).toBeNull()
  })

  it("returns null when the operator does not apply to the field type", () => {
    // « > » is a number operator; acteur_id is text
    expect(rowToClause({ field: "acteur_id", operator: ">", value: "5" })).toBeNull()
  })
})

describe("buildDjangoQL", () => {
  it("joins clauses with and", () => {
    expect(
      buildDjangoQL(
        [
          { field: "has_parent", operator: "=", value: "true" },
          { field: "statut", operator: "=", value: "AVALIDER" },
        ],
        "and",
      ),
    ).toBe('has_parent = True and statut = "AVALIDER"')
  })

  it("joins clauses with or", () => {
    expect(
      buildDjangoQL(
        [
          { field: "id", operator: "=", value: "1" },
          { field: "id", operator: "=", value: "2" },
        ],
        "or",
      ),
    ).toBe("id = 1 or id = 2")
  })

  it("skips incomplete rows", () => {
    expect(
      buildDjangoQL(
        [
          { field: "acteur_id", operator: "=", value: "" },
          { field: "id", operator: "=", value: "7" },
        ],
        "and",
      ),
    ).toBe("id = 7")
  })

  it("returns an empty string when nothing is valid", () => {
    expect(buildDjangoQL([blankRow()], "and")).toBe("")
  })
})

describe("operatorsForField", () => {
  it("offers text operators for a text field", () => {
    const ops = operatorsForField("contexte").map((operator) => operator.value)
    expect(ops).toContain("~")
    expect(ops).not.toContain(">")
  })

  it("offers numeric comparators for a number field", () => {
    const ops = operatorsForField("id").map((operator) => operator.value)
    expect(ops).toContain(">")
    expect(ops).not.toContain("~")
  })

  it("offers only equality operators for a bool field", () => {
    const ops = operatorsForField("has_parent").map((operator) => operator.value)
    expect(ops).toEqual(["=", "!="])
  })
})
