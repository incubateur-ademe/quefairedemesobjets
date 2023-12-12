import { Controller } from "@hotwired/stimulus"
import { SolutionMap } from "./solution_map"
import { Actor } from "./types"
const debounce = require("lodash/debounce")

export default class extends Controller<HTMLElement> {
    static targets = ["acteur", "searchInZone", "bBox"]
    declare readonly acteurTargets: Array<HTMLScriptElement>
    declare readonly searchInZoneTarget: HTMLButtonElement
    declare readonly bBoxTarget?: HTMLScriptElement

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
        if (this.hasBBoxTarget) {
            const bbox = JSON.parse(this.bBoxTarget.textContent)
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
        console.log("mapChanged !!!", event.detail)
        this.searchInZoneTarget.name = "search_in_zone"
        this.searchInZoneTarget.value = JSON.stringify(event.detail)
        this.displaySearchInZoneButton()
    }

    displaySearchInZoneButton() {
        this.searchInZoneTarget.classList.remove("qfdmo-hidden")
    }

    hideSearchInZoneButton() {
        this.searchInZoneTarget.classList.add("qfdmo-hidden")
    }
}
