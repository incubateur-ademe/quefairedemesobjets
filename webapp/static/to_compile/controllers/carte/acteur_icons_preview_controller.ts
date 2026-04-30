import { Controller } from "@hotwired/stimulus"
import { addOverlay, mapStyles, Overlay } from "carte-facile"
import maplibregl from "maplibre-gl"
import { _internals, iconNameFor, registerActeurIcons } from "../../js/acteur_icons"

class ActeurIconsPreviewController extends Controller<HTMLElement> {
  static targets = ["mapContainer"]
  declare readonly mapContainerTarget: HTMLDivElement

  async connect() {
    const map = new maplibregl.Map({
      container: this.mapContainerTarget,
      style: mapStyles.desaturated,
      center: [2.213749, 46.227638],
      zoom: 5.5,
      attributionControl: { compact: true },
    })

    addOverlay(map, Overlay.administrativeBoundaries)

    await new Promise<void>((resolve) => map.on("load", () => resolve()))
    await registerActeurIcons(map)

    // Expose for pixel-diff testing in the preview harness.
    ;(window as unknown as { _previewMap?: typeof map })._previewMap = map

    // One feature per (variant × bonus) at a stable spot so we can eyeball
    // each variant. Lay them out across France in a row so all are visible at
    // initial zoom.
    const features = _internals.GROUPE_ACTION_VARIANTS.flatMap((variant, index) => {
      const lng = -3 + index * 1.6
      return [false, true].map((bonus, row) => ({
        type: "Feature" as const,
        geometry: {
          type: "Point" as const,
          coordinates: [lng, 47.5 - row * 1.4],
        },
        properties: {
          icon: iconNameFor(variant.code, bonus),
          label: `${variant.code}${bonus ? " + bonus" : ""}`,
        },
      }))
    })

    map.addSource("acteurs-preview", {
      type: "geojson",
      data: { type: "FeatureCollection", features },
    })

    map.addLayer({
      id: "acteurs-preview-layer",
      type: "symbol",
      source: "acteurs-preview",
      layout: {
        "icon-image": ["get", "icon"],
        // Anchor the bottom-tip of the pin (with bonus protrusion accounted for
        // by the SVG's outer canvas height) to the geographic point. Today's
        // DOM pinpoints anchor on the point too via the maplibre default.
        "icon-anchor": "bottom",
        "icon-allow-overlap": true,
        "icon-ignore-placement": true,
        "text-field": ["get", "label"],
        "text-font": ["Open Sans Regular"],
        "text-offset": [0, 1],
        "text-anchor": "top",
        "text-size": 11,
        "text-allow-overlap": true,
      },
      paint: {
        "text-halo-color": "#fff",
        "text-halo-width": 1.5,
      },
    })
  }
}

export default ActeurIconsPreviewController
