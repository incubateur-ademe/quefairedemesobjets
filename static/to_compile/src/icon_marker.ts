import L from "leaflet"
import "leaflet-extra-markers/dist/js/leaflet.extra-markers.min.js"

export const defaultMarker = L.ExtraMarkers.icon({
    icon: "fr-icon-checkbox-circle-line",
    markerColor: "#000",
    shape: "square",
    prefix: "qfdmo-icon",
    svg: true,
})
