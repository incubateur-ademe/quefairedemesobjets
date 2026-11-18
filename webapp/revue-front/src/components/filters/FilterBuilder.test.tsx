import { fireEvent, render, screen } from "@testing-library/react"

import type { FilterField } from "../../api/types"
import { setControlValue } from "../../test-utils"
import { FilterBuilder } from "./FilterBuilder"

const FIELDS: FilterField[] = [
  {
    key: "identifiant_action",
    label: "Identifiant de l'action",
    famille: "cohorte",
    type: "text",
    operateurs: ["icontains", "eq", "is_empty"],
  },
  {
    key: "type_action",
    label: "Type d'action",
    famille: "cohorte",
    type: "choice",
    operateurs: ["eq", "in"],
    choix: [{ value: "SOURCE_AJOUT", label: "Ajout" }],
  },
]

describe("FilterBuilder", () => {
  it("builds a condition and applies the API filter", () => {
    const onApply = jest.fn()
    render(
      <FilterBuilder
        fields={FIELDS}
        value={{ op: "and", conditions: [] }}
        onApply={onApply}
      />,
    )

    fireEvent.click(screen.getByText("+ Condition"))
    setControlValue(screen.getByLabelText("Valeur"), "ecomaison", "input")
    fireEvent.click(screen.getByText("au moins une (OU)"))
    fireEvent.submit(screen.getByText("Appliquer").closest("form")!)

    expect(onApply).toHaveBeenCalledWith({
      op: "or",
      conditions: [
        { field: "identifiant_action", operator: "icontains", value: "ecomaison" },
      ],
    })
  })

  it("resets the operator and value when the field changes", () => {
    const onApply = jest.fn()
    render(
      <FilterBuilder
        fields={FIELDS}
        value={{
          op: "and",
          conditions: [{ field: "identifiant_action", operator: "eq", value: "x" }],
        }}
        onApply={onApply}
      />,
    )

    setControlValue(screen.getByLabelText("Champ"), "type_action")
    setControlValue(screen.getByLabelText("Valeur"), "SOURCE_AJOUT")
    fireEvent.submit(screen.getByText("Appliquer").closest("form")!)

    expect(onApply).toHaveBeenCalledWith({
      op: "and",
      conditions: [{ field: "type_action", operator: "eq", value: "SOURCE_AJOUT" }],
    })
  })

  it("clears everything", () => {
    const onApply = jest.fn()
    render(
      <FilterBuilder
        fields={FIELDS}
        value={{
          op: "and",
          conditions: [{ field: "identifiant_action", operator: "is_empty" }],
        }}
        onApply={onApply}
      />,
    )

    fireEvent.click(screen.getByText("Tout effacer"))

    expect(onApply).toHaveBeenCalledWith({ op: "and", conditions: [] })
    expect(screen.queryByLabelText("Champ")).not.toBeInTheDocument()
  })
})
