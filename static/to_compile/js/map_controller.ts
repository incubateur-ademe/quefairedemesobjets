import { Controller } from "@hotwired/stimulus"
import * as Turbo from "@hotwired/turbo"
import debounce from "lodash/debounce"
import { SolutionMap } from "./solution_map"
import { ActorLocation, DisplayedActeur } from "./types"
import { removeHash } from "./helpers"

export class Actor implements DisplayedActeur {
  identifiant_unique: string
  location: ActorLocation
  icon: string
  couleur: string
  bonus: boolean
  reparer: boolean

  constructor(actorFields: DisplayedActeur) {
    this.identifiant_unique = actorFields.identifiant_unique
    this.location = actorFields.location
    this.icon = actorFields.icon
    this.couleur = actorFields.couleur
    this.bonus = actorFields.bonus
    this.reparer = actorFields.reparer
  }
}

export default class extends Controller<HTMLElement> {
  static targets = ["acteur", "searchInZoneButton", "bbox"]
  static values = {
    location: { type: Object, default: {} },
  }
  declare readonly acteurTargets: Array<HTMLScriptElement>
  declare readonly searchInZoneButtonTarget: HTMLButtonElement
  declare readonly bboxTarget: HTMLInputElement
  declare readonly hasBboxTarget: boolean
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
          const actor_fields: DisplayedActeur = JSON.parse(ecoCirTarget.textContent)
          return new Actor(actor_fields)
        }
      })
      .filter((actor) => actor !== undefined)
    if (this.hasBboxTarget && this.bboxTarget.value !== "") {
      const bbox = JSON.parse(this.bboxTarget.value)
      actorsMap.addActorMarkersToMap(actors, bbox)
    } else {
      actorsMap.addActorMarkersToMap(actors)
    }

    actorsMap.initEventListener()
    removeHash()
  }

  initialize() {
    this.mapChanged = debounce(this.mapChanged, 300).bind(this)
  }

  mapChanged(event: CustomEvent) {
    this.dispatch("updateBbox", { detail: event.detail })
    this.displaySearchInZoneButton()
  }

  displaySearchInZoneButton() {
    this.searchInZoneButtonTarget.classList.remove("qf-hidden")
  }

  hideSearchInZoneButton() {
    this.searchInZoneButtonTarget.classList.add("qf-hidden")
  }
}
