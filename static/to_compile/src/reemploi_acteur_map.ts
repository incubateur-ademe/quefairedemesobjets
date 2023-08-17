import L from 'leaflet';

export class ReemploiActeurMap {
    #map: L.Map
    constructor() {
        var map = L.map('map')
        map.setView([48.940158, 2.349521], 13);
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© OpenStreetMap'
        }).addTo(map);
        var marker = L.marker([48.940158, 2.349521]).addTo(map);
        marker.bindPopup("<p><strong>Vous êtes ici !</strong></b>").openPopup();
    }
}
