import "@testing-library/jest-dom"

import { Application } from "@hotwired/stimulus"
import SearchSolutionFormController from "../js/search_solution_form_controller"

describe("SearchSolutionFormController", () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <div data-controller="search-solution-form">
                <fieldset data-search-solution-form-target="direction">
                    <input type="radio" name="direction" value="jai" data-action="click->search-solution-form#changeDirection" id="id_direction_0" checked="">
                    <input type="radio" name="direction" value="jecherche" data-action="click->search-solution-form#changeDirection" id="id_direction_1">
                </fieldset>
                <button type="button" data-action="search-solution-form#toggleadvancedFiltersDiv" data-search-solution-form-target="advancedFiltersButton">
                    <span class="qf-hidden" data-search-solution-form-target="advancedFiltersCounter"></span>
                </button>
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

        expect(jechercheTarget).not.toBeVisible()
        expect(jaiTarget).toBeVisible()
    })

    it("click jecherche option display jecherche target and hide advancedFilters", async () => {
        const jechercheOption = document.getElementById("id_direction_1")
        jechercheOption?.click()
        await new Promise((r) => setTimeout(r, 0))

        const jechercheTarget = document.querySelector(
            '[data-search-solution-form-target="jecherche"]',
        )
        const jaiTarget = document.querySelector(
            '[data-search-solution-form-target="jai"]',
        )

        expect(jechercheTarget).toBeVisible()
        expect(jaiTarget).not.toBeVisible()
    })
})
