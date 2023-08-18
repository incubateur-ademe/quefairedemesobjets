import L from 'leaflet';

const DEFAULT_LOACTION: Array<Number> = [46.227638, 2.213749]
const DEFAULT_ZOOM: Number = 5
const DEFAULT_MAX_ZOOM: Number = 19

export interface Location {
    geometry?: {
      coordinates: number[];
    };
}

export class ReemploiActeurMap {
    #map: L.Map
    constructor(
        {location, reemploiacteurs}: {location: Location, reemploiacteurs: Array<HTMLScriptElement>}
    ) {
        this.#map = L.map('map', {
            preferCanvas: true
        })

        let points: Array<Array<Number>> = []
        this.#map.setView(DEFAULT_LOACTION, DEFAULT_ZOOM);
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: DEFAULT_MAX_ZOOM,
            attribution: '© OpenStreetMap'
        }).addTo(this.#map);
        if (location.hasOwnProperty('geometry')) {
            L.marker([
                location.geometry?.coordinates[1],
                location.geometry?.coordinates[0]
            ])
                .addTo(this.#map)
                .bindPopup("<p><strong>Vous êtes ici !</strong></b>").openPopup();
        }
        reemploiacteurs.forEach(function (reemploiacteur: HTMLScriptElement) {
            if (reemploiacteur.textContent !== null) {
                const reemploiacteur_fields = JSON.parse(reemploiacteur.textContent)
                L.marker([
                    reemploiacteur_fields.location.coordinates[1],
                    reemploiacteur_fields.location.coordinates[0]
                ])
                    .addTo(this.#map)
                    .bindPopup("<p><strong>" + reemploiacteur_fields.nom + "</strong></b>");
                points.push([
                    reemploiacteur_fields.location.coordinates[1],
                    reemploiacteur_fields.location.coordinates[0]
                ]);
            }
        }, this);
        if (points.length > 0) {
            this.#map.fitBounds(points);
        }


    }
}
