import { Controller } from "@hotwired/stimulus"
import debounce from "lodash/debounce"
import { SolutionMap } from "./solution_map"
import { Actor } from "./types"

export default class extends Controller<HTMLElement> {
    static targets = ["acteur", "searchInZoneButton", "bBox"]
    declare readonly acteurTargets: Array<HTMLScriptElement>
    declare readonly searchInZoneButtonTarget: HTMLButtonElement
    declare readonly bboxTarget: HTMLInputElement

    declare readonly hasBboxTarget: boolean

    static values = { location: { type: Object, default: {} } }
    declare readonly locationValue: object

    connect() {
        const actorsMap = new SolutionMap({
            location: this.locationValue,
            controller: this,
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
        if (this.hasBboxTarget && this.bboxTarget.value !== "") {
            const bbox = JSON.parse(this.bboxTarget.value)
            actorsMap.displayActor(actors, bbox)
        } else {
            actorsMap.displayActor(actors)
        }

        actorsMap.initEventListener()
    }
    initialize() {
        this.mapChanged = debounce(this.mapChanged, 300).bind(this)
    }

    mapChanged(event: CustomEvent) {
        this.dispatch("searchInZone", { detail: event.detail })
        this.displaySearchInZoneButton()
    }

    displaySearchInZoneButton() {
        this.searchInZoneButtonTarget.classList.remove("qfdmo-hidden")
    }

    hideSearchInZoneButton() {
        this.searchInZoneButtonTarget.classList.add("qfdmo-hidden")
    }

    displayActorDetail(identifiantUnique: string) {
        this.dispatch("displayDetails", { detail: {} })
        this.dispatch("setSrcDetailsAddress", {
            detail: { identifiantUnique: identifiantUnique },
        })
    }
}
