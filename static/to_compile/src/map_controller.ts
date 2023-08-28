import { Controller } from "@hotwired/stimulus"
import { EconomieCirculaireSolutionMap } from "./economie_circulaire_acteur_map"
import { Actor } from "./types"

export default class extends Controller<HTMLElement> {
    static targets = ["economiecirculaireacteur"]
    declare readonly economiecirculaireacteurTargets: Array<HTMLScriptElement>

    static values = { location: { type: Object, default: {} } }
    declare readonly locationValue: object

    connect() {
        const actorsMap = new EconomieCirculaireSolutionMap({
            location: this.locationValue,
        })
        //fixme : find how do not allow undefined from map
        const actors: Array<Actor> = this.economiecirculaireacteurTargets
            .map((ecoCirTarget: HTMLScriptElement) => {
                if (ecoCirTarget.textContent !== null) {
                    const actor_fields = JSON.parse(ecoCirTarget.textContent)
                    return new Actor(actor_fields)
                }
            })
            .filter((actor) => actor !== undefined)

        actorsMap.display_actor(actors)
    }
}
