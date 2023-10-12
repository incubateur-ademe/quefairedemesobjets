import L from "leaflet"
import "leaflet-extra-markers/dist/js/leaflet.extra-markers.min.js"

export const homeIconMarker = L.ExtraMarkers.icon({
    icon: "fr-icon-home-4-line",
    markerColor: "black",
    prefix: "qfdmo-icon",
})

export const defaultMarker = L.ExtraMarkers.icon({
    icon: "fr-icon-checkbox-circle-line",
    markerColor: "#000",
    shape: "square",
    prefix: "qfdmo-icon",
    svg: true,
})
