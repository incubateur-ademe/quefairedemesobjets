import { Controller } from "@hotwired/stimulus"
import debounce from "lodash/debounce"
import { removeHash } from "../../js/helpers"
import { SolutionMap } from "../../js/solution_map"
import { ActorLocation, DisplayedActeur } from "../../js/types"
import SearchFormController from "./search_solution_form_controller"

export class Actor implements DisplayedActeur {
  uuid: string
  fillBackground: boolean
  location: ActorLocation
  icon: string
  iconFile: string
  couleur: string
  bonus: boolean
  reparer: boolean

  constructor(actorFields: DisplayedActeur) {
    this.uuid = actorFields.uuid
    this.location = actorFields.location
    this.icon = actorFields.icon
    this.iconFile = actorFields.iconFile
    this.fillBackground = actorFields.fillBackground
    this.couleur = actorFields.couleur
    this.bonus = actorFields.bonus
    this.reparer = actorFields.reparer
  }
}

class MapController extends Controller<HTMLElement> {
  static targets = ["acteur", "searchInZoneButton", "bbox", "mapContainer"]
  static values = {
    location: { type: Object, default: {} },
    initialZoom: Number,
  }
  declare readonly acteurTargets: Array<HTMLElement>
  declare readonly searchInZoneButtonTarget: HTMLButtonElement
  declare readonly hasSearchInZoneButtonTarget: boolean
  declare readonly bboxTarget: HTMLInputElement
  declare readonly mapContainerTarget: HTMLDivElement
  declare readonly hasBboxTarget: boolean
  declare readonly locationValue: object
  declare readonly initialZoomValue: number

  connect() {
    const actorsMap = new SolutionMap({
      selector: this.mapContainerTarget,
      location: this.locationValue,
      initialZoom: this.initialZoomValue,
      controller: this,
    })

    if (this.hasBboxTarget && this.bboxTarget.value !== "") {
      const bbox = JSON.parse(this.bboxTarget.value)
      actorsMap.addActorMarkersToMap(this.acteurTargets, bbox)
    } else {
      actorsMap.addActorMarkersToMap(this.acteurTargets)
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
    if (this.hasSearchInZoneButtonTarget) {
      this.searchInZoneButtonTarget.classList.remove("qf-hidden")
    }
  }

  hideSearchInZoneButton() {
    if (this.hasSearchInZoneButtonTarget) {
      this.searchInZoneButtonTarget.classList.add("qf-hidden")
    }
  }

  setActiveActeur(uuid: string) {
    // We do not use Stimulus outlets or events here so that the event does
    // not dispatch to all controller's instances.
    // This way, the selcted acteur won't open on Bon Etat and Mauvais Etat panels.
    const solutionForm: SearchFormController =
      this.application.getControllerForElementAndIdentifier(
        this.element.closest("[data-controller='search-solution-form']")!,
        "search-solution-form",
      ) as SearchFormController

    solutionForm.displayActeur(uuid)
  }
}
export default MapController
