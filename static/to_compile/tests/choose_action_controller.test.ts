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
                <div data-search-solution-form-target="jai"></div>
                <div data-search-solution-form-target="jecherche"></div>
                <div data-search-solution-form-target="apply"></div>
                <input data-search-solution-form-target="actionList" />
            </div>
        `
        const application = Application.start()
        application.register("search-solution-form", SearchSolutionFormController)
    })

    it("default display jai or jecherche target", () => {
        const jechercheTarget = document.querySelector(
            '[search-solution-form-action-target="jecherche"]',
        )
        const jaiTarget = document.querySelector(
            '[search-solution-form-action-target="jai"]',
        )
        expect(jechercheTarget).not.toBeVisible()
        expect(jaiTarget).toBeVisible()
    })

    it("click jecherche option display jecherche target", async () => {
        const jechercheOption = document.getElementById("id_direction_1")
        jechercheOption.click()
        await new Promise((r) => setTimeout(r, 0))

        const jechercheTarget = document.querySelector(
            '[search-solution-form-action-target="jecherche"]',
        )
        const jaiTarget = document.querySelector(
            '[search-solution-form-action-target="jai"]',
        )
        expect(jechercheTarget).toBeVisible()
        expect(jaiTarget).not.toBeVisible()
    })
})
