import "@testing-library/jest-dom"

import { Application } from "@hotwired/stimulus"
import SearchSolutionFormController from "../src/search_solution_form_controller"

describe("SearchSolutionFormController", () => {
    let controller
    let application
    beforeEach(() => {
        document.body.innerHTML = `
            <div data-controller="search-solution-form">
                <fieldset data-search-solution-form-target="direction">
                    <input type="radio" name="direction" value="jai" data-action="click->search-solution-form#changeDirection" id="id_direction_0" checked="">
                    <input type="radio" name="direction" value="jecherche" data-action="click->search-solution-form#changeDirection" id="id_direction_1">
                </fieldset>
                <div data-search-solution-form-target="advancedFiltersButton"></div>
                <button type="button" data-action="click -> search-solution-form#toggleadvancedFiltersDiv" data-search-solution-form-target="advancedFiltersButton">
                    <span class="qfdmo-hidden" data-search-solution-form-target="advancedFiltersCounter"></span>
                </button>
                <div data-search-solution-form-target="advancedFiltersDiv">
                    <input
                        type="checkbox"
                        data-search-solution-form-target="advancedFiltersField"
                        data-action="click -> search-solution-form#updateAdvancedFiltersCounter">
                    <input type="checkbox" name="advanced_filters" value="1" data-action="change->search-solution-form#updateAdvancedFiltersCounter" id="id_advanced_filters">
                </div>
                <div data-action="click->search-solution-form#apply">
                    <input name="reparer" id="jai_reparer" data-search-solution-form-target="action" type="checkbox" checked="" data-action="click -> search-solution-form#updateSearchSolutionForm">
                </div>
                <div data-search-solution-form-target="jai"></div>
                <div data-search-solution-form-target="jecherche"></div>
                <input data-search-solution-form-target="actionList" />
            </div>
        `
        const application = Application.start()
        application.register("search-solution-form", SearchSolutionFormController)
    })

    it("default display jai or jecherche target", async () => {
        await new Promise((r) => setTimeout(r, 0))

        const jechercheTarget = document.querySelector(
            '[data-search-solution-form-target="jecherche"]',
        )
        const jaiTarget = document.querySelector(
            '[data-search-solution-form-target="jai"]',
        )
        const advancedFiltersDivTarget = document.querySelector(
            '[data-search-solution-form-target="advancedFiltersDiv"]',
        )
        const advancedFiltersButtonTarget = document.querySelector(
            '[data-search-solution-form-target="advancedFiltersButton"]',
        )

        expect(jechercheTarget).not.toBeVisible()
        expect(jaiTarget).toBeVisible()
        expect(advancedFiltersDivTarget).not.toHaveClass("qfdmo-hidden")
        expect(advancedFiltersButtonTarget).not.toHaveClass("qfdmo-hidden")
    })

    it("click jecherche option display jecherche target and hide advancedFilters", async () => {
        const jechercheOption = document.getElementById("id_direction_1")
        jechercheOption.click()
        await new Promise((r) => setTimeout(r, 0))

        const jechercheTarget = document.querySelector(
            '[data-search-solution-form-target="jecherche"]',
        )
        const jaiTarget = document.querySelector(
            '[data-search-solution-form-target="jai"]',
        )
        const advancedFiltersDivTarget = document.querySelector(
            '[data-search-solution-form-target="advancedFiltersDiv"]',
        )
        const advancedFiltersButtonTarget = document.querySelector(
            '[data-search-solution-form-target="advancedFiltersButton"]',
        )

        expect(jechercheTarget).toBeVisible()
        expect(jaiTarget).not.toBeVisible()
        expect(advancedFiltersDivTarget).toHaveClass("qfdmo-hidden")
        expect(advancedFiltersButtonTarget).toHaveClass("qfdmo-hidden")
    })

    it("click jai et reparer option display advancedFilters", async () => {
        const jaiOption = document.getElementById("id_direction_0")
        jaiOption.click()
        const reparerOption = document.getElementById("jai_reparer") as HTMLInputElement
        reparerOption.checked = true
        reparerOption.dispatchEvent(new Event("click"))
        await new Promise((r) => setTimeout(r, 0))

        const advancedFiltersDivTarget = document.querySelector(
            '[data-search-solution-form-target="advancedFiltersDiv"]',
        )
        const advancedFiltersButtonTarget = document.querySelector(
            '[data-search-solution-form-target="advancedFiltersButton"]',
        )

        expect(advancedFiltersDivTarget).not.toHaveClass("qfdmo-hidden")
        expect(advancedFiltersButtonTarget).not.toHaveClass("qfdmo-hidden")
    })

    it("Check jai, reparer et advancedFiltersField option display and set advancedFiltersCounter", async () => {
        const jaiOption = document.getElementById("id_direction_0")
        jaiOption.click()
        const reparerOption = document.getElementById("jai_reparer") as HTMLInputElement
        reparerOption.checked = true
        const advancedFiltersField = document.querySelector(
            '[data-search-solution-form-target="advancedFiltersField"]',
        ) as HTMLInputElement
        advancedFiltersField.checked = false
        advancedFiltersField.click() // check it
        await new Promise((r) => setTimeout(r, 0))

        const advancedFiltersCounterTarget = document.querySelector(
            '[data-search-solution-form-target="advancedFiltersCounter"]',
        ) as HTMLElement

        expect(advancedFiltersCounterTarget.innerText).toEqual("1")
        expect(advancedFiltersCounterTarget).not.toHaveClass("qfdmo-hidden")
    })

    it("Check jai, reparer and uncheck advancedFiltersField option hide advancedFiltersCounter", async () => {
        const jaiOption = document.getElementById("id_direction_0")
        jaiOption.click()
        const reparerOption = document.getElementById("jai_reparer") as HTMLInputElement
        reparerOption.checked = true
        const advancedFiltersField = document.querySelector(
            '[data-search-solution-form-target="advancedFiltersField"]',
        ) as HTMLInputElement
        advancedFiltersField.checked = true
        advancedFiltersField.click() // check it
        await new Promise((r) => setTimeout(r, 0))

        const advancedFiltersCounterTarget = document.querySelector(
            '[data-search-solution-form-target="advancedFiltersCounter"]',
        ) as HTMLElement

        expect(advancedFiltersCounterTarget).toHaveClass("qfdmo-hidden")
    })
})
