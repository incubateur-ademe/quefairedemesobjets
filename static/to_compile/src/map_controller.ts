import { Controller } from "@hotwired/stimulus"
import { SolutionMap } from "./solution_map"
import { Actor } from "./types"

export default class extends Controller<HTMLElement> {
    static targets = ["acteur"]
    declare readonly acteurTargets: Array<HTMLScriptElement>

    static values = { location: { type: Object, default: {} } }
    declare readonly locationValue: object

    connect() {
        const actorsMap = new SolutionMap({
            location: this.locationValue,
        })
        //fixme : find how do not allow undefined from map
        const actors: Array<Actor> = this.acteurTargets
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
