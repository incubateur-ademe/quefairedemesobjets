import bonusIconSvg from "bundle-text:../svg/bonus-reparation-fill.svg"
import pinBackgroundFillSvg from "bundle-text:../svg/pin-background-fill.svg"
import pinBackgroundSvg from "bundle-text:../svg/pin-background.svg"
import * as L from "leaflet"
import { ACTIVE_PINPOINT_CLASSNAME, clearActivePinpoints } from "./helpers"
import MapController from "./map_controller"
import type { DisplayedActeur, Location, LVAOMarker } from "./types"

const DEFAULT_LOCATION: L.LatLngTuple = [46.227638, 2.213749]
const DEFAULT_ZOOM: number = 5
const DEFAULT_MAX_ZOOM: number = 19

export class SolutionMap {
  map: L.Map
  #zoomControl: L.Control.Zoom
  #location: Location
  #mapWidthBeforeResize: number
  #controller: MapController
  bboxValue?: Array<Number>
  points: Array<Array<Number>>

  constructor({
    location,
    controller,
  }: {
    location: Location
    controller: MapController
  }) {
    this.#location = location
    this.#controller = controller
    this.map = L.map("map", {
      preferCanvas: true,
      zoomControl: false,
    })

    this.map.setView(DEFAULT_LOCATION, DEFAULT_ZOOM)
    L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png", {
      maxZoom: DEFAULT_MAX_ZOOM,
      attribution:
        "© <a href='https://www.openstreetmap.org/copyright' rel='noopener'>OpenStreetMap</a>",
    }).addTo(this.map)
    L.control.scale({ imperial: false }).addTo(this.map)
    this.#manageZoomControl()

    if (
      this.#location.latitude !== undefined &&
      this.#location.longitude !== undefined
    ) {
      const homeIcon = L.divIcon({
        className: "!qf-z-[10000]",
        iconSize: [35, 35],
        html: this.#generateHomeHTMLString(),
      })

      L.marker([this.#location.latitude, this.#location.longitude], {
        icon: homeIcon,
      })
        .addTo(this.map)
        .bindPopup("<p><strong>Vous êtes ici !</strong></b>")
    }
  }

  #generateHomeHTMLString() {
    return `<div class="qf-flex qf-items-center qf-justify-center qf-rounded-full qf-bg-white qf-aspect-square qf-border-2 qf-border-solid qf-border-[#E1000F]">
      <span class="fr-icon-map-pin-2-fill qf-text-[#E1000F]"></span>
    </div>
    `
  }

  #generateMarkerHTMLStringFrom(acteur?: DisplayedActeur): string {
    const markerHtmlStyles = `color: ${acteur?.couleur};`
    const background = acteur?.reparer ? pinBackgroundFillSvg : pinBackgroundSvg
    const cornerIcon = acteur?.bonus ? bonusIconSvg : ""
    const icon = acteur?.icon || "fr-icon-checkbox-circle-line"
    const markerIconClasses = `qf-absolute qf-top-[10] qf-left-[10.5] qf-margin-auto
      ${icon} ${acteur?.reparer ? "qf-text-white" : ""}
    `
    const htmlTree = [
      `<div data-animated class="qf-scale-75">`,
      `<div class="qf--translate-y-2/4" style="${markerHtmlStyles}">`,
      background,
    ]
    if (cornerIcon) {
      htmlTree.push(
        `<span class="qf-absolute qf-right-[-16] qf-top-[-6] qf-z-10">`,
        cornerIcon,
        `</span>`,
      )
    }
    htmlTree.push(`<span class="${markerIconClasses}"></span>`, `</div>`, `</div>`)
    return htmlTree.join("")
  }

  addActorMarkersToMap(
    actors: Array<DisplayedActeur>,
    bboxValue?: Array<Number>,
  ): void {
    const points: Array<Array<Number>> = []
    actors.forEach(function (actor: DisplayedActeur) {
      if (actor.location) {
        const markerHtmlString = this.#generateMarkerHTMLStringFrom(actor)
        const actorMarker = L.divIcon({
          // Empty className ensures default leaflet classes are not added,
          // they add styles like a border and a background to the marker
          className: "",
          iconSize: [34, 45],
          html: markerHtmlString,
        })

        const marker: LVAOMarker = L.marker(
          [actor.location.coordinates[1], actor.location.coordinates[0]],
          {
            icon: actorMarker,
            riseOnHover: true,
          },
        )
        marker._uuid = actor.uuid
        marker.on("click", (e) => {
          this.#onClickMarker(e)
        })
        marker.on("keydown", (e) => {
          // Open solution details when user presses enter or spacebar keys
          if ([32, 13].includes(e.originalEvent.keyCode)) {
            this.#onClickMarker(e)
          }
        })
        marker.addTo(this.map)
        points.push([actor.location.coordinates[1], actor.location.coordinates[0]])
      }
    }, this)
    if (
      this.#location.latitude !== undefined &&
      this.#location.longitude !== undefined
    ) {
      points.push([this.#location.latitude, this.#location.longitude])
    }
    this.fitBounds(points, bboxValue)
  }

  fitBounds(points, bboxValue) {
    this.points = points
    this.bboxValue = bboxValue
    if (typeof bboxValue !== "undefined") {
      this.map.fitBounds([
        [bboxValue.southWest.lat, bboxValue.southWest.lng],
        [bboxValue.northEast.lat, bboxValue.northEast.lng],
      ])
    } else if (points.length > 0) {
      this.map.fitBounds(points)
    }
  }

  #onClickMarker(event: L.LeafletEvent) {
    clearActivePinpoints()
    event.target._icon.classList.add(ACTIVE_PINPOINT_CLASSNAME)
    window.location.hash = event.target._uuid
  }

  #manageZoomControl() {
    this.#zoomControl = L.control.zoom({ position: "topleft" })
    this.#zoomControl.addTo(this.map)
  }

  #dispatchMapChangedEvent(e: L.LeafletEvent): void {
    const bounds = e.target.getBounds()
    const detail = {
      center: bounds.getCenter(),
      southWest: bounds.getSouthWest(),
      northEast: bounds.getNorthEast(),
    }
    const event = new CustomEvent("leaflet:mapChanged", {
      detail,
      bubbles: true,
    })
    this.#controller.mapChanged(event)
  }

  initEventListener(): void {
    // Map width is set here so that it can be compared during each resize.
    // If the map container grew, the value should be different, hence
    // considering the map to not be idle.
    // Once the mapWidth has stopped growing, we can consider the map as idle
    // and add events that will help set its boundaries and zoom level.
    this.#mapWidthBeforeResize = this.map.getSize().x

    const resizeObserver = new ResizeObserver(() => {
      this.map.invalidateSize({ pan: false })
      this.fitBounds(this.points, this.bboxValue)
      const currentMapWidth = this.map.getSize().x
      const resizeStopped =
        this.#mapWidthBeforeResize > 0 && this.#mapWidthBeforeResize === currentMapWidth

      if (resizeStopped) {
        // The 1s timeout here is arbitrary and prevents adding listener
        // when the map is still moving.
        setTimeout(() => {
          this.map.on("moveend", this.#dispatchMapChangedEvent.bind(this))
          resizeObserver.disconnect()
        }, 1000)
      }
      this.#mapWidthBeforeResize = currentMapWidth
    })

    resizeObserver.observe(this.map.getContainer())
  }
}
