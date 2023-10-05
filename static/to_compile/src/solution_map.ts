import L from "leaflet"
import "leaflet-extra-markers/dist/js/leaflet.extra-markers.min.js"
import { defaultMarker, homeIconMarker } from "./icon_marker"
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
    "yellow-tournesol": "#C8AA39",
    "yellow-moutarde": "#C3992A",
    "orange-terre-battue": "#E4794A",
    "brown-cafe-creme": "#D1B781",
    "brown-caramel": "#C08C65",
    "brown-opera": "#BD987A",
    "beige-gris-galet": "#AEA397",
}

function get_color_code(colorName: string): string {
    if (colorName in COLOR_MAPPING) {
        return COLOR_MAPPING[colorName]
    }
    return "#000"
}

export class SolutionMap {
    #map: L.Map
    #location: Location
    constructor({ location }: { location: Location }) {
        this.#location = location
        this.#map = L.map("map", {
            preferCanvas: true,
        })

        this.#map.setView(DEFAULT_LOCATION, DEFAULT_ZOOM)
        L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: DEFAULT_MAX_ZOOM,
            attribution: "© OSM",
        }).addTo(this.#map)
        L.control.scale({ imperial: false }).addTo(this.#map)
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

    display_actor(actors: Array<Actor>): void {
        let points: Array<Array<Number>> = []

        actors.forEach(function (actor: Actor) {
            if (actor.location) {
                var customMarker = undefined
                if (actor.actions.length > 0) {
                    console.log(actor.actions[0])
                    customMarker = L.ExtraMarkers.icon({
                        icon: actor.actions[0].icon,
                        markerColor: get_color_code(actor.actions[0].couleur),
                        shape: "square",
                        prefix: "qfdmo-icon",
                        svg: true,
                    })
                } else {
                    customMarker = defaultMarker
                }
                L.marker(
                    [actor.location.coordinates[1], actor.location.coordinates[0]],
                    {
                        icon: customMarker,
                        riseOnHover: true,
                    },
                )
                    .addTo(this.#map)
                    .bindPopup(actor.render_as_card)
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

        if (points.length > 0) {
            this.#map.fitBounds(points)
        }
    }

    get_map(): L.Map {
        return this.#map
    }
}
