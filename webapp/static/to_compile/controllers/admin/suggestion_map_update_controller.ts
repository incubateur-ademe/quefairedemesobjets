import { Controller } from "@hotwired/stimulus"
import { postFieldsValues } from "./suggestion_post"

export default class extends Controller<HTMLElement> {
  static values = {
    updateUrl: String,
    fieldsGroups: String,
  }

  declare readonly updateUrlValue: string
  declare readonly fieldsGroupsValue: string

  handleMarkerDragged(event: CustomEvent) {
    const { latitude, longitude, markerElement } = event.detail
    const markerKey = markerElement.dataset.markerKey
    if (!latitude || !longitude) {
      console.error("Coordonnées manquantes dans l'événement")
      return
    }
    if (!markerKey) {
      console.error("Clé du marker manquante dans l'élément")
      return
    }

    postFieldsValues(
      this.element,
      this.updateUrlValue,
      markerKey,
      { latitude, longitude },
      this.fieldsGroupsValue,
      "localisation",
    )
  }
}
