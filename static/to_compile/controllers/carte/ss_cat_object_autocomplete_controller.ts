import posthog from "posthog-js"
import AutocompleteController from "./autocomplete_controller"

export default class extends AutocompleteController {
  controllerName: string = "ss-cat-object-autocomplete"

  static values = {
    onlyReemploi: Boolean,
    ...AutocompleteController.values,
  }

  declare readonly onlyReemploiValue: boolean

  static targets = AutocompleteController.targets.concat(["ssCat"])
  declare readonly ssCatTarget: HTMLInputElement

  async searchToComplete(events: Event): Promise<void> {
    const inputTargetValue = this.inputTarget.value
    const val = this.addAccents(inputTargetValue)
    const regexPattern = new RegExp(val, "gi")

    if (!val) this.hideAutocompleteList()

    let countResult = 0

    return this.#getOptionCallback(inputTargetValue)
      .then((data) => {
        this.hideAutocompleteList()
        if (data.length == 0) return

        this.autocompleteList = this.createAutocompleteList()
        for (let i = 0; i < data.length; i++) {
          if (countResult >= this.maxOptionDisplayedValue) break
          countResult++
          this.addOption(regexPattern, data[i])
        }
        if (this.autocompleteList.childElementCount > 0) {
          this.currentFocusedOptionIndexValue = 0
        }

        posthog.capture("object_input", {
          object_requested: inputTargetValue,
          object_list: data ? data.slice(0, this.maxOptionDisplayedValue) : undefined,
          first_object: data ? data[0]["label"] : undefined,
          first_subcategory: data ? data[0]["sub_label"] : undefined,
        })
      })
      .then(() => {
        this.spinnerTarget.classList.add("qf-hidden")
        return
      })
  }

  selectOption(event: Event) {
    const inputTargetValue = this.inputTarget.value

    let target = event.target as HTMLElement
    while (target && target.nodeName !== "DIV") {
      target = target.parentNode as HTMLElement
    }
    const option = JSON.parse(target.getElementsByTagName("input")[0].value)
    const labelValue = option.label
    const subLabelValue = option.sub_label
    const identifierValue = option.identifier

    this.inputTarget.value = labelValue
    this.ssCatTarget.value = identifierValue

    this.hideAutocompleteList()
    // Call outlet
    this.dispatch("optionSelected")
  }

  keydownEnter(event: KeyboardEvent): boolean {
    let toSubmit = super.keydownEnter(event)
    if (toSubmit) {
      this.dispatch("formSubmit")
    }
    return toSubmit
  }

  async #getOptionCallback(value: string): Promise<object[]> {
    if (value.trim().length < this.nbCharToSearchValue) {
      this.ssCatTarget.value = ""
      return []
    }
    let get_synonymes_url = `/qfdmo/get_synonyme_list?q=${value}`
    if (this.onlyReemploiValue) {
      get_synonymes_url += `&only_reemploi=true`
    }
    return await fetch(get_synonymes_url)
      .then((response) => response.json())
      .then((data) => {
        return data
      })
      .catch((error) => {
        console.error("error catched : ", error)
        return []
      })
  }
}
