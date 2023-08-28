import { Controller } from "@hotwired/stimulus"
import { EconomieCirculaireSolutionMap } from "./economie_circulaire_acteur_map"

export default class extends Controller<HTMLElement> {
    static targets = ["economiecirculaireacteur"]
    declare readonly economiecirculaireacteurTargets: Array<HTMLScriptElement>

    static values = { location: { type: Object, default: {} } }
    declare readonly locationValue: object

    connect() {
        new EconomieCirculaireSolutionMap({
            location: this.locationValue,
            economiecirculaireacteurs: this.economiecirculaireacteurTargets,
        })
    }
}
