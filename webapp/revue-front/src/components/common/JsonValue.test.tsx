import { render, screen, within } from "@testing-library/react"

import { JsonEntries, toTable } from "./JsonValue"

const PAR_CHAMP = {
  " ": ["MODIF", "SUP", "AJOUT"],
  nom: [1, 0, 0],
  telephone: [0, 0, 15],
}

describe("toTable", () => {
  it("reads a header key with a blank name", () => {
    expect(toTable(PAR_CHAMP)).toEqual({
      columns: ["MODIF", "SUP", "AJOUT"],
      rows: [
        { label: "nom", cells: [1, 0, 0] },
        { label: "telephone", cells: [0, 0, 15] },
      ],
    })
  })

  it("reads arrays without header and lists of flat objects", () => {
    expect(toTable({ a: [1, 2], b: [3, 4] })?.columns).toEqual(["1", "2"])
    expect(toTable([{ champ: "nom", n: 1 }, { champ: "email" }])).toEqual({
      columns: ["champ", "n"],
      rows: [
        { label: "1", cells: ["nom", 1] },
        { label: "2", cells: ["email", undefined] },
      ],
    })
  })

  it.each([
    24,
    "texte",
    { a: 1 },
    { a: [1, 2], b: [3] },
    { a: [{ x: 1 }] },
    [1, 2],
    [],
  ])("is not a table: %j", (value) => {
    expect(toTable(value)).toBeNull()
  })
})

describe("JsonEntries", () => {
  it("renders tabular JSON as a table and scalars as text", () => {
    render(
      <JsonEntries
        entries={[
          ["Nombre de mises à jour par champ", PAR_CHAMP],
          ["Nombre d'acteurs à mettre à jour", 24],
        ]}
      />,
    )

    const table = screen.getByRole("table")
    expect(
      within(table)
        .getAllByRole("columnheader")
        .map((th) => th.textContent),
    ).toEqual(["", "MODIF", "SUP", "AJOUT"])
    expect(
      within(table).getByRole("rowheader", { name: "telephone" }),
    ).toBeInTheDocument()
    expect(screen.getByText("24")).toBeInTheDocument()
    expect(screen.queryByText(/metadata\./)).not.toBeInTheDocument()
  })
})
