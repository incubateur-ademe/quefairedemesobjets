import { Controller } from "@hotwired/stimulus"
import { ReemploiSolutionMap } from "./reemploi_acteur_map"

export default class extends Controller<HTMLElement> {
    static targets = ["reemploiacteur"]
    declare readonly reemploiacteurTargets: Array<HTMLScriptElement>

    static values = { location: { type: Object, default: {} } }
    declare readonly locationValue: object

    initialize() {
        new ReemploiSolutionMap({
            location: this.locationValue,
            reemploiacteurs: this.reemploiacteurTargets,
        })
    }
}
