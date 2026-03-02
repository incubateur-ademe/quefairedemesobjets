/* global ol */
import { Controller } from "@hotwired/stimulus"

// Geocoding address search controller for the Django admin map widget.
//
// Usage (rendered by custom-openlayers-with-search.html):
//
//   <div data-controller="map-search"
//        data-map-search-widget-id-value="<textarea_id>"
//        data-map-search-address-field-ids-value="id_adresse,id_adresse_complement,id_code_postal,id_ville"
//   >
//     <input data-map-search-target="input" type="text" />
//     <input type="button" data-action="click->map-search#search" value="Placer sur la carte" />
//   </div>
//
// On connect(), the input is pre-filled by joining the values of the listed
// address fields with ", " as separator.

export default class extends Controller<HTMLElement> {
  static targets = ["input"]
  static values = {
    widgetId: String,
    addressFieldIds: String,
  }

  declare readonly inputTarget: HTMLInputElement
  declare readonly widgetIdValue: string
  declare readonly addressFieldIdsValue: string

  connect() {
    if (!this.addressFieldIdsValue) return
    const ids = this.addressFieldIdsValue.split(",").map((s) => s.trim())
    const parts: string[] = []
    for (const id of ids) {
      const el = document.getElementById(id) as HTMLInputElement | null
      if (el?.value) parts.push(el.value)
    }
    if (parts.length) this.inputTarget.value = parts.join(", ")
  }

  async search(event: Event) {
    event.preventDefault()
    const address = this.inputTarget.value.trim()
    if (!address) return

    const url = `https://data.geopf.fr/geocodage/search/?q=${encodeURIComponent(address)}&limit=1`
    let data: any
    try {
      const response = await fetch(url)
      data = await response.json()
    } catch (error) {
      console.error("Geocoding request failed:", error)
      return
    }

    const feature = data?.features?.[0]
    if (!feature) {
      console.warn("No geocoding result for:", address)
      return
    }

    const [lon, lat] = feature.geometry.coordinates
    const widget = (window as any).geodjangoWidgets?.[this.widgetIdValue]
    if (!widget) {
      console.error("Map widget not found for id:", this.widgetIdValue)
      return
    }

    widget.clearFeatures()
    const point = new (ol as any).Feature({
      geometry: new (ol as any).geom.Point((ol as any).proj.fromLonLat([lon, lat])),
    })
    widget.featureCollection.push(point)
    widget.map.setView(
      new (ol as any).View({
        center: (ol as any).proj.fromLonLat([lon, lat]),
        zoom: 15,
      }),
    )
  }
}
