/* global ol */
import { Controller } from "@hotwired/stimulus"

// Geocoding address search controller for the Django admin map widget.
//
// Usage (rendered by custom-openlayers-with-search.html):
//
//   <div data-controller="map-search"
//        data-map-search-widget-id-value="<textarea_id>"
//        data-map-search-initial-value="<address string">
//   >
//     <input data-map-search-target="input" type="text" />
//     <button data-action="map-search#search">Placer sur la carte</button>
//   </div>

export default class extends Controller<HTMLElement> {
  static targets = ["input"]
  static values = { widgetId: String }

  declare readonly inputTarget: HTMLInputElement
  declare readonly widgetIdValue: string

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
    // Set the serialized textarea value directly (EPSG:4326 coordinates)
    ;(document.getElementById(widget.options.id) as HTMLTextAreaElement).value =
      `{ "type": "Point", "coordinates": [ ${lon}, ${lat} ] }`
    // Add the projected feature to the map
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
