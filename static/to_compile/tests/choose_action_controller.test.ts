import "@testing-library/jest-dom"

import { Application } from "@hotwired/stimulus"
import ChooseActionController from "../src/choose_action_controller"

describe("ChooseActionController", () => {
    let controller
    let application
    beforeEach(() => {
        document.body.innerHTML = `
            <div data-controller="choose-action">
                <fieldset data-choose-action-target="direction">
                    <input type="radio" name="direction" value="jai" data-action="click->choose-action#changeDirection" id="id_direction_0" checked="">
                    <input type="radio" name="direction" value="jecherche" data-action="click->choose-action#changeDirection" id="id_direction_1">
                </fieldset>
                <fieldset data-choose-action-target="overwrittenDirection">
                    <input type="radio" name="direction" value="jai" data-action="click->choose-action#changeDirection" id="id_direction_2" checked="">
                    <input type="radio" name="direction" value="jecherche" data-action="click->choose-action#changeDirection" id="id_direction_3">
                </fieldset>
                <div data-choose-action-target="jai"></div>
                <div data-choose-action-target="jecherche"></div>
                <div data-choose-action-target="apply"></div>
                <input data-choose-action-target="actionList" />
            </div>
        `
        const application = Application.start()
        application.register("choose-action", ChooseActionController)
    })

    it("default display jai or jecherche target", () => {
        const jechercheTarget = document.querySelector(
            '[data-choose-action-target="jecherche"]',
        )
        const jaiTarget = document.querySelector('[data-choose-action-target="jai"]')
        expect(jechercheTarget).not.toBeVisible()
        expect(jaiTarget).toBeVisible()
    })

    // FIXME: doesn't work because it submit the form
    // it("click jecherche option display jecherche target", () => {
    //     const jechercheOption = document.getElementById("id_direction_1")
    //     jechercheOption.click()

    //     const jechercheTarget = document.querySelector(
    //         '[data-choose-action-target="jecherche"]',
    //     )
    //     const jaiTarget = document.querySelector('[data-choose-action-target="jai"]')
    //     expect(jechercheTarget).toBeVisible()
    //     expect(jaiTarget).not.toBeVisible()
    // })
})
