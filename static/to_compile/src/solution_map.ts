import L from "leaflet"
import "leaflet-extra-markers/dist/js/leaflet.extra-markers.min.js"
import { defaultMarker, homeIconMarker } from "./icon_marker"
import MapController from "./map_controller"
import { Actor, Location } from "./types"

const DEFAULT_LOCATION: Array<Number> = [46.227638, 2.213749]
const DEFAULT_ZOOM: Number = 5
const DEFAULT_MAX_ZOOM: Number = 19
const COLOR_MAPPING: object = {
    "blue-france": "#0055FF",
    "green-tilleul-verveine": "#B7A73F",
    "green-bourgeon": "#68A532",
    "green-emeraude": "#00A95F",
    "green-menthe": "#009081",
    "green-archipel": "#009099",
    "blue-ecume": "#465F9D",
    "blue-cumulus": "#417DC4",
    "purple-glycine": "#A558A0",
    "pink-macaron": "#E18B76",
    "pink-tuile": "#CE614A",
    "yellow-tournesol": "#e9c53b",
    "yellow-moutarde": "#C3992A",
    "orange-terre-battue": "#E4794A",
    "brown-cafe-creme": "#D1B781",
    "brown-caramel": "#C08C65",
    "brown-opera": "#BD987A",
    "beige-gris-galet": "#AEA397",
    "pink-tuile-850": "#fcbfb7",
    "green-menthe-850": "#73e0cf",
    "green-bourgeon-850": "#95e257",
    "yellow-moutarde-850": "#fcc63a",
    "blue-ecume-850": "#bfccfb",
    "green-menthe-sun-373": "#37635f",
    "blue-cumulus-sun-368": "#3558A2",
    "orange-terre-battue-main-645": "#E4794A",
    "brown-cafe-creme-main-782": "#D1B781",
    "purple-glycine-main-494": "#A558A0",
    "green-menthe-main-548": "#009081",
}

function get_color_code(colorName: string): string {
    if (colorName in COLOR_MAPPING) {
        return COLOR_MAPPING[colorName]
    }
    return "#000"
}

export class SolutionMap {
    #map: L.Map
    #zoomControl: L.Control.Zoom
    #location: Location
    #controller: MapController

    constructor({
        location,
        controller,
    }: {
        location: Location
        controller: MapController
    }) {
        this.#location = location
        this.#controller = controller
        this.#map = L.map("map", {
            preferCanvas: true,
            zoomControl: false,
        })

        this.#map.setView(DEFAULT_LOCATION, DEFAULT_ZOOM)
        L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png", {
            maxZoom: DEFAULT_MAX_ZOOM,
            attribution:
                "© <a href='https://www.openstreetmap.org/copyright' rel='noopener'>OpenStreetMap</a>",
        }).addTo(this.#map)
        L.control.scale({ imperial: false }).addTo(this.#map)
        this.#manageZoomControl()

        if (
            this.#location.latitude !== undefined &&
            this.#location.longitude !== undefined
        ) {
            L.marker([this.#location.latitude, this.#location.longitude], {
                icon: homeIconMarker,
            })
                .addTo(this.#map)
                .bindPopup("<p><strong>Vous êtes ici !</strong></b>")
        }
    }

    displayActor(actors: Array<Actor>, bbox?: Array<Number>): void {
        let points: Array<Array<Number>> = []

        actors.forEach(function (actor: Actor) {
            if (actor.location) {
                // Create the marker look and feel : pin + icon
                var customMarker = undefined
                if (actor.actions.length > 0) {
                    customMarker = L.ExtraMarkers.icon({
                        icon: actor.acteur_selected_action.icon,
                        markerColor: get_color_code(
                            actor.acteur_selected_action.couleur,
                        ),
                        shape: "square",
                        prefix: "qfdmo-icon",
                        svg: true,
                    })
                } else {
                    customMarker = defaultMarker
                }

                // create the marker on map
                let marker = L.marker(
                    [actor.location.coordinates[1], actor.location.coordinates[0]],
                    {
                        icon: customMarker,
                        riseOnHover: true,
                    },
                )
                marker._identifiant_unique = actor.identifiant_unique
                marker.on("click", (e) => {
                    this.#onClickMarker(e)
                })
                marker.addTo(this.#map)

                points.push([
                    actor.location.coordinates[1],
                    actor.location.coordinates[0],
                ])
            }
        }, this)
        if (
            this.#location.latitude !== undefined &&
            this.#location.longitude !== undefined
        ) {
            points.push([this.#location.latitude, this.#location.longitude])
        }
        if (bbox !== undefined) {
            this.#map.fitBounds([
                [bbox[1], bbox[0]],
                [bbox[3], bbox[2]],
            ])
        } else if (points.length > 0) {
            this.#map.fitBounds(points)
        }
    }

    get_map(): L.Map {
        return this.#map
    }

    #onClickMarker(event: L.LeafletEvent) {
        this.#controller.displayActorDetail(event.target._identifiant_unique)
    }

    #manageZoomControl() {
        this.#zoomControl = L.control.zoom({ position: "topleft" })
        this.#zoomControl.addTo(this.#map)
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
        this.#map.on("moveend", this.#dispatchMapChangedEvent.bind(this))
    }
}
