import * as L from "leaflet"
import MapController from "./map_controller"
import pinBackgroundSvg from "bundle-text:./svg/pin-background.svg"
import pinBackgroundFillSvg from "bundle-text:./svg/pin-background-fill.svg"
import bonusIconSvg from "bundle-text:../entrypoints/svg/bonus-reparation-fill.svg"
import { ACTIVE_PINPOINT_CLASSNAME, clearActivePinpoints } from "./map_helpers"
import type { DisplayedActeur, Location, LVAOMarker } from "./types"

const DEFAULT_LOCATION: L.LatLngTuple = [46.227638, 2.213749]
const DEFAULT_ZOOM: number = 5
const DEFAULT_MAX_ZOOM: number = 19

// TODO : handle directly from DSFR module
const COLOR_MAPPING: object = {
  "beige-gris-galet": "#AEA397",
  "blue-cumulus-sun-368": "#3558A2",
  "blue-cumulus": "#417DC4",
  "blue-ecume-850": "#bfccfb",
  "blue-ecume": "#465F9D",
  "blue-france": "#0055FF",
  "brown-cafe-creme-main-782": "#D1B781",
  "brown-cafe-creme": "#D1B781",
  "brown-caramel": "#C08C65",
  "brown-opera": "#BD987A",
  "green-archipel": "#009099",
  "green-bourgeon-850": "#95e257",
  "green-bourgeon": "#68A532",
  "green-emeraude": "#00A95F",
  "green-menthe-850": "#73e0cf",
  "green-menthe-main-548": "#009081",
  "green-menthe-sun-373": "#37635f",
  "green-menthe": "#009081",
  "green-tilleul-verveine": "#B7A73F",
  "orange-terre-battue-main-645": "#E4794A",
  "orange-terre-battue": "#E4794A",
  "pink-macaron": "#E18B76",
  "pink-tuile-850": "#fcbfb7",
  "pink-tuile": "#CE614A",
  "purple-glycine-main-494": "#A558A0",
  "purple-glycine": "#A558A0",
  "yellow-moutarde-850": "#fcc63a",
  "yellow-moutarde": "#C3992A",
  "yellow-tournesol": "#e9c53b",
  "brown-caramel-sun-425-hover": "#bb8568"
}

function get_color_code(colorName: string): string {
  if (colorName in COLOR_MAPPING) {
    return COLOR_MAPPING[colorName]
  }
  return "#000"
}

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
        className: "!qfdmo-z-[10000]",
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
    return `<div class="qfdmo-flex qfdmo-items-center qfdmo-justify-center qfdmo-rounded-full qfdmo-bg-white qfdmo-aspect-square qfdmo-border-2 qfdmo-border-solid qfdmo-border-[#E1000F]">
      <span class="fr-icon-map-pin-2-fill qfdmo-text-[#E1000F]"></span>
    </div>
    `
  }

  #generateMarkerHTMLStringFrom(actor?: DisplayedActeur): string {
    const markerHtmlStyles = `color: ${get_color_code(actor?.couleur || "")};`
    const background = actor?.reparer ? pinBackgroundFillSvg : pinBackgroundSvg
    const cornerIcon = actor?.bonus ? bonusIconSvg : ""
    const icon = actor?.icon || "fr-icon-checkbox-circle-line"
    const markerIconClasses = `qfdmo-absolute qfdmo-top-[10] qfdmo-left-[10.5] qfdmo-margin-auto
      ${icon} ${actor?.reparer ? "qfdmo-text-white" : ""}
    `
    const htmlTree = [
      `<div data-animated class="qfdmo-scale-75">`,
      `<div class="qfdmo--translate-y-2/4" style="${markerHtmlStyles}">`,
      background,
    ]
    if (cornerIcon) {
      htmlTree.push(
        `<span class="qfdmo-absolute qfdmo-right-[-16] qfdmo-top-[-6] qfdmo-z-10">`,
        cornerIcon,
        `</span>`,
      )
    }
    htmlTree.push(`<span class="${markerIconClasses}"></span>`, `</div>`, `</div>`)
    return htmlTree.join("")
  }

  displayActor(actors: Array<DisplayedActeur>, bboxValue?: Array<Number>): void {
    let points: Array<Array<Number>> = []
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
        marker._identifiant_unique = actor.identifiant_unique
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
    if (bboxValue !== undefined) {
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
    this.#controller.displayActorDetail(event.target._identifiant_unique)
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
