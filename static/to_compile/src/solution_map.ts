import L from "leaflet"
import { Actor, Location } from "./types"

const DEFAULT_LOCATION: Array<Number> = [46.227638, 2.213749]
const DEFAULT_ZOOM: Number = 5
const DEFAULT_MAX_ZOOM: Number = 19

import { homeIconMarker, redMarker } from "./icon_marker"

export class SolutionMap {
    #map: L.Map
    constructor({ location }: { location: Location }) {
        this.#map = L.map("map", {
            preferCanvas: true,
        })

        this.#map.setView(DEFAULT_LOCATION, DEFAULT_ZOOM)
        L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: DEFAULT_MAX_ZOOM,
            attribution: "© OpenStreetMap",
        }).addTo(this.#map)
        if (location.latitude !== undefined && location.longitude !== undefined) {
            L.marker(
                [location.latitude, location.longitude],
                // [location.geometry?.coordinates[1], location.geometry?.coordinates[0]],
                { icon: homeIconMarker },
            )
                .addTo(this.#map)
                .bindPopup("<p><strong>Vous êtes ici !</strong></b>")
        }
    }

    display_actor(actors: Array<Actor>): void {
        let points: Array<Array<Number>> = []

        actors.forEach(function (actor: Actor) {
            let popupContent = actor.popupTitle() + actor.popupContent()

            if (actor.location) {
                L.marker(
                    [actor.location.coordinates[1], actor.location.coordinates[0]],
                    {
                        icon: redMarker,
                    },
                )
                    .addTo(this.#map)
                    .bindPopup(popupContent)
                points.push([
                    actor.location.coordinates[1],
                    actor.location.coordinates[0],
                ])
            }
        }, this)
        if (points.length > 0) {
            this.#map.fitBounds(points)
        }
    }
}
