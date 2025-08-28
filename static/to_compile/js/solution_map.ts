import bonusIconSvg from "bundle-text:../svg/bonus-reparation-fill.svg"
import pinBackgroundFillSvg from "bundle-text:../svg/pin-background-fill.svg"
import pinBackgroundSvg from "bundle-text:../svg/pin-background.svg"
import maplibregl, { LngLat, LngLatBoundsLike, Map, Marker } from "maplibre-gl"
import "maplibre-gl/dist/maplibre-gl.css"
import MapController from "../controllers/carte/map_controller"
import { ACTIVE_PINPOINT_CLASSNAME, clearActivePinpoints } from "./helpers"
import type { DisplayedActeur, Location } from "./types"
const DEFAULT_LOCATION: LngLat = new LngLat(2.213749, 46.227638)
const DEFAULT_ZOOM: number = 5
const DEFAULT_MAX_ZOOM: number = 18

export class SolutionMap {
  map: Map
  #location: Location
  #mapWidthBeforeResize: number
  #controller: MapController
  bboxValue?: Array<Number>
  points: Array<Array<Number>>
  mapPadding: number = 50

  constructor({
    selector,
    location,
    controller,
  }: {
    selector: HTMLDivElement
    location: Location
    controller: MapController
  }) {
    this.#location = location
    this.#controller = controller

    this.map = new Map({
      container: selector,
      style: {
        version: 8,
        sources: {
          "carto-light": {
            type: "raster",
            tiles: [
              "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
              "https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
              "https://c.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
            ],
            tileSize: 256,
            attribution: "© OpenStreetMap contributors, © CARTO",
          },
        },
        layers: [
          {
            id: "carto-light-layer",
            type: "raster",
            source: "carto-light",
            minzoom: 0,
            maxzoom: 19,
          },
        ],
      },
      center: DEFAULT_LOCATION,
      zoom: DEFAULT_ZOOM,
      maxZoom: DEFAULT_MAX_ZOOM,
      // Ajouter les contrôles de zoom
    })
    this.#manageZoomControl()

    if (
      this.#location.latitude !== undefined &&
      this.#location.longitude !== undefined
    ) {
      new maplibregl.Marker({
        element: this.#generateHomeHTMLMarker(),
      })
        .setLngLat([this.#location.longitude, this.#location.latitude])
        .setPopup(
          new maplibregl.Popup().setHTML("<p><strong>Vous êtes ici !</strong></p>"),
        )
        .addTo(this.map)
    }
  }

  #generateHomeHTMLMarker() {
    const el = document.createElement("div")
    el.innerHTML = `<div class="qf-flex qf-items-center qf-justify-center qf-rounded-full qf-bg-white qf-aspect-square qf-border-2 qf-border-solid qf-border-[#E1000F]">
      <span class="fr-icon-map-pin-2-fill qf-text-[#E1000F]"></span>
    </div>
    `
    el.className = "!qf-z-[10000] home-icon"
    el.style.width = "35px"
    el.style.height = "35px"
    return el
  }

  #generateMarkerHTMLStringFrom(acteur?: DisplayedActeur): string {
    /**
    This method uses complex scale and translate css attributes in
    order to compensate an issue that causes the marker to not be
    at the location it is supposed to be when zooming in / out.

    This could definitely be fixed by using appropriately sized
    svg, but works fine as is.

    If you need to add a new marker's design in the future, it
    is advised to follow the approach to not this bug.
    */
    if (acteur?.iconFile) {
      return [
        `<div data-animated class="qf-scale-75">`,
        `<img class="qf--translate-y-2/4" height="61" width="46" src="${acteur.iconFile}">`,
        `</div>`,
      ].join("")
    }

    const markerHtmlStyles = `color: ${acteur?.couleur};`
    let background: string = acteur?.fillBackground
      ? pinBackgroundFillSvg
      : pinBackgroundSvg
    if (background.includes("MASK_ID")) {
      // When multiple maps are displayed in DSFR tabs, a bug occurs because pins mask share
      // the same id : #a.
      // This bug causes the mask to briefly appears then disappear, and the pin's border gets lost.
      // The fix here is to hardcode a magical MASK_ID value for the id's value in the svg file, and
      // replace it with the acteur's id. Therefore, we ensure the mask ids are always unique and
      // this prevents the bug to occur.
      background = background.replace(/MASK_ID/g, acteur?.uuid!)
    }

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

  #generateMarkerHTMLMarker(acteur?: DisplayedActeur): HTMLDivElement {
    const actorMarker = document.createElement("div")
    actorMarker.innerHTML = this.#generateMarkerHTMLStringFrom(acteur)
    actorMarker.className = ""
    actorMarker.style.width = "34px"
    actorMarker.style.height = "45px"
    actorMarker.dataset.uuid = acteur?.uuid || ""
    actorMarker.addEventListener("click", () => {
      this.#onClickMarker(actorMarker)
    })
    return actorMarker
  }

  addActorMarkersToMap(
    actors: Array<DisplayedActeur>,
    bboxValue?: Array<Number>,
  ): void {
    const points: Array<Array<Number>> = []
    const addedActors: Array<string> = []
    actors.forEach(function (actor: DisplayedActeur) {
      if (addedActors.includes(actor.uuid)) {
        // Ensure actors are not added twice on the map.
        // This can happen and can causes visual glitches.
        // ID of markers being duplicated, these are wrongly rendered
        // without borders.
        return
      }
      if (actor.location) {
        const actorMarker = this.#generateMarkerHTMLMarker(actor)

        const marker: Marker = new maplibregl.Marker({
          element: actorMarker,
        }).setLngLat([actor.location.coordinates[0], actor.location.coordinates[1]])

        marker.addTo(this.map)
        addedActors.push(actor.uuid)
        points.push([actor.location.coordinates[1], actor.location.coordinates[0]])
      }
    }, this)
    this.fitBounds(points, bboxValue)
  }

  fitBounds(points, bboxValue) {
    this.points = points
    this.bboxValue = bboxValue
    if (typeof bboxValue !== "undefined") {
      this.map.fitBounds(
        [
          [bboxValue.southWest.lng, bboxValue.southWest.lat],
          [bboxValue.northEast.lng, bboxValue.northEast.lat],
        ],
        {
          padding: this.mapPadding,
          duration: 0,
        },
      )
    } else if (points.length > 0) {
      // Compute bbox from points
      const lngs = points.map((point) => point[1])
      const lats = points.map((point) => point[0])
      const bounds: LngLatBoundsLike = [
        [Math.min(...lngs), Math.min(...lats)], // Sud-ouest
        [Math.max(...lngs), Math.max(...lats)], // Nord-est
      ]
      this.map.fitBounds(bounds, {
        padding: this.mapPadding,
        duration: 0,
      })
    }
  }

  #onClickMarker(actorMarker: HTMLDivElement) {
    clearActivePinpoints()
    actorMarker.classList.add(ACTIVE_PINPOINT_CLASSNAME)
    this.#controller.setActiveActeur(actorMarker.dataset.uuid || "")
  }

  #manageZoomControl() {
    this.map.addControl(
      new maplibregl.NavigationControl({
        visualizePitch: false,
        visualizeRoll: false,
        showZoom: true,
        showCompass: false,
      }),
      "top-left",
    )
  }

  #dispatchMapChangedEvent(): void {
    const bounds = this.map.getBounds()
    const detail = {
      center: bounds.getCenter(),
      southWest: bounds.getSouthWest(),
      northEast: bounds.getNorthEast(),
    }
    const event = new CustomEvent("maplibre:mapChanged", {
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
    this.#mapWidthBeforeResize = this.map.getContainer().offsetWidth
    const resizeObserver = new ResizeObserver(() => {
      this.map.resize()
      this.fitBounds(this.points, this.bboxValue)
      const currentMapWidth = this.map.getContainer().offsetWidth
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
