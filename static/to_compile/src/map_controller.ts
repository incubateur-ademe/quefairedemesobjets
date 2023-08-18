import { Controller } from "@hotwired/stimulus";
import L from 'leaflet';

export default class extends Controller<HTMLElement> {
    static targets = ["reemploiacteur"];
    readonly reemploiacteurTarget: HTMLScriptElement
    readonly reemploiacteurTargets: Array<HTMLScriptElement>

    static values = {
        location: {type: Object, default: {}}
    }
    readonly locationValue: object

    initialize() {
        var map = L.map('map')
        let points: Array<Array<Number>> = []
        map.setView([48.940158, 2.349521], 13);
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© OpenStreetMap'
        }).addTo(map);
        if (this.locationValue.geometry !== undefined) {
            L.marker([
                this.locationValue.geometry.coordinates[1],
                this.locationValue.geometry.coordinates[0]
            ])
                .addTo(map)
                .bindPopup("<p><strong>Vous êtes ici !</strong></b>").openPopup();
        }
        this.reemploiacteurTargets.forEach(function (reemploiacteur: HTMLScriptElement) {
            const reemploiacteur_fields = JSON.parse(reemploiacteur.textContent)
            L.marker([
                reemploiacteur_fields.location.coordinates[1],
                reemploiacteur_fields.location.coordinates[0]
            ])
                .addTo(map)
                .bindPopup("<p><strong>" + reemploiacteur_fields.nom + "</strong></b>");
            points.push([
                reemploiacteur_fields.location.coordinates[1],
                reemploiacteur_fields.location.coordinates[0]
            ]);
        });
        map.fitBounds(points);

    }
}

