import L from "leaflet"

const DEFAULT_LOACTION: Array<Number> = [46.227638, 2.213749]
const DEFAULT_ZOOM: Number = 5
const DEFAULT_MAX_ZOOM: Number = 19

import { homeIconMarker, redMarker } from "./icon_marker"

export interface Location {
    geometry?: {
        coordinates: number[]
    }
}

export class EconomieCirculaireSolutionMap {
    #map: L.Map
    constructor({
        location,
        economiecirculaireacteurs,
    }: {
        location: Location
        economiecirculaireacteurs: Array<HTMLScriptElement>
    }) {
        this.#map = L.map("map", {
            preferCanvas: true,
        })

        let points: Array<Array<Number>> = []
        this.#map.setView(DEFAULT_LOACTION, DEFAULT_ZOOM)
        L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: DEFAULT_MAX_ZOOM,
            attribution: "© OpenStreetMap",
        }).addTo(this.#map)
        if (location.hasOwnProperty("geometry")) {
            L.marker(
                [location.geometry?.coordinates[1], location.geometry?.coordinates[0]],
                { icon: homeIconMarker },
            )
                .addTo(this.#map)
                .bindPopup("<p><strong>Vous êtes ici !</strong></b>")
                .openPopup()
        }
        economiecirculaireacteurs.forEach(function (
            economiecirculaireacteur: HTMLScriptElement,
        ) {
            if (economiecirculaireacteur.textContent !== null) {
                const economiecirculaireacteur_fields = JSON.parse(
                    economiecirculaireacteur.textContent,
                )
                let popupContent =
                    "<p><strong>" +
                    economiecirculaireacteur_fields.nom +
                    "</strong></b><br>"
                let proposition_services =
                    economiecirculaireacteur_fields.proposition_services
                for (let i = 0; i < proposition_services.length; i++) {
                    let action = proposition_services[i].action.nom
                    popupContent = popupContent + action + "<br>"
                    let acteur_service = proposition_services[i].acteur_service.nom
                    popupContent = popupContent + acteur_service + "<br>"
                    let sous_categories = proposition_services[i].sous_categories
                    for (var j = 0; j < sous_categories.length; j++) {
                        popupContent = popupContent + sous_categories[j].nom + ", "
                    }
                }

                L.marker(
                    [
                        economiecirculaireacteur_fields.location.coordinates[1],
                        economiecirculaireacteur_fields.location.coordinates[0],
                    ],
                    { icon: redMarker },
                )
                    .addTo(this.#map)
                    .bindPopup(popupContent)
                points.push([
                    economiecirculaireacteur_fields.location.coordinates[1],
                    economiecirculaireacteur_fields.location.coordinates[0],
                ])
            }
        }, this)
        if (points.length > 0) {
            this.#map.fitBounds(points)
        }
    }
}
