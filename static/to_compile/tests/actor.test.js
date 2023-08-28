const { Actor } = require("../src/types")
// FIXME : make the ES6 syntax worls with ts-jest and parcel
//import { Actor } from "../src/types"

describe("sum module", () => {
    test("Actor title", () => {
        let actor = new Actor({ nom: "My name !" })
        expect(actor.popupTitle()).toBe("<p><strong>My name !</strong></b><br>")
    })
})
