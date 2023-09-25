import L from "leaflet"
import "leaflet-extra-markers/dist/js/leaflet.extra-markers.min.js"

console.log(L)
export const homeIconMarker = L.ExtraMarkers.icon({
    icon: "fr-icon-home-4-line",
    markerColor: "blue",
    prefix: "qfdmo-icon",
})

export const redMarker = L.ExtraMarkers.icon({
    icon: "fr-icon-checkbox-circle-line",
    markerColor: "red",
    shape: "square",
    prefix: "qfdmo-icon",
})
