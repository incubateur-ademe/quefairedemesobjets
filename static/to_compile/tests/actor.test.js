/**
 * @jest-environment jsdom
 */

const { Actor } = require("../src/types")
// FIXME : make the ES6 syntax worls with ts-jest and parcel
//import { Actor } from "../src/types"

describe("Actor class popupTitle", () => {
    test("Actor title from nom", () => {
        let actor = new Actor({ nom: "My name !" })
        expect(actor.popupTitle()).toBe('<h5 class="fr-mb-0">My name !</h5>')
    })
    test("Actor title empty nom_commercial", () => {
        let actor = new Actor({
            nom: "My name !",
            nom_commercial: "",
        })
        expect(actor.popupTitle()).toBe('<h5 class="fr-mb-0">My name !</h5>')
    })
    test("Actor title from commercial nom", () => {
        let actor = new Actor({
            nom: "My name !",
            nom_commercial: "My commercial name !",
        })
        expect(actor.popupTitle()).toBe('<h5 class="fr-mb-0">My commercial name !</h5>')
    })
})

describe("Actor class popupContent", () => {
    test("Actor without details", () => {
        let actor = new Actor({})
        expect(actor.popupContent()).toBe("<div></div>")
    })
    test("Actor with address", () => {
        let actor = new Actor({
            adresse: "My address !",
            adresse_complement: "My address complement !",
            code_postal: "My postal code !",
            ville: "My ville !",
        })
        expect(actor.popupContent()).toBe(
            "<div>My address !<br>My address complement !<br>My postal code ! My ville !<br></div>",
        )
    })
    test("Actor with tel and url", () => {
        let actor = new Actor({
            telephone: "01 02 03 04 05",
            url: "www.example.com",
        })
        expect(actor.popupContent()).toBe(
            '<div>01 02 03 04 05<br><a href="www.example.com" target="_blank">www.example.com</a></div>',
        )
    })
})
