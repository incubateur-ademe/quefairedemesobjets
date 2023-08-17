import { Controller } from "@hotwired/stimulus";
import L from 'leaflet';

export default class extends Controller<HTMLElement> {
    static targets = ["latitude", "longitude"];
    readonly latitudeTarget: HTMLInputElement
    readonly longitudeTarget: HTMLInputElement
    initialize() {
        const latitude = this.latitudeTarget.value;
        const longitude = this.longitudeTarget.value;
        var map = L.map('map')
        map.setView([48.940158, 2.349521], 13);
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© OpenStreetMap'
        }).addTo(map);
        var marker = L.marker([latitude, longitude]).addTo(map);
        marker.bindPopup("<p><strong>Vous êtes ici !</strong></b>").openPopup();
    }
}

