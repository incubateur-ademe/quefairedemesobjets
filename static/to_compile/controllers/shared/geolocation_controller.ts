import { Controller } from "@hotwired/stimulus"

export default class GeolocationController extends Controller {
  requestLocation(event: Event) {
    event.preventDefault()

    if (!("geolocation" in navigator)) {
      this.dispatch("error", {
        detail: {
          message: "La géolocalisation n'est pas disponible sur votre appareil",
        },
      })
      return
    }

    // Dispatch loading event
    this.dispatch("loading")

    navigator.geolocation.getCurrentPosition(
      (position) => this.onSuccess(position),
      (error) => this.onError(error),
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      },
    )
  }

  onSuccess(position: GeolocationPosition) {
    const latitude = position.coords.latitude
    const longitude = position.coords.longitude
    const labelValue = "Autour de moi"

    // Dispatch to global state (matches address_autocomplete_controller behavior)
    this.dispatchLocationToGlobalState(
      labelValue,
      latitude.toString(),
      longitude.toString(),
    )

    this.dispatch("success", {
      detail: {
        latitude,
        longitude,
        address: labelValue,
      },
    })
  }

  dispatchLocationToGlobalState(adresse: string, latitude: string, longitude: string) {
    this.dispatch("change", { detail: { adresse, latitude, longitude } })
  }

  onError(error: GeolocationPositionError) {
    let message = "La géolocalisation est inaccessible sur votre appareil"

    switch (error.code) {
      case error.PERMISSION_DENIED:
        message = "Vous avez refusé l'accès à votre position"
        break
      case error.POSITION_UNAVAILABLE:
        message = "Votre position n'a pas pu être déterminée"
        break
      case error.TIMEOUT:
        message = "La demande de géolocalisation a expiré"
        break
    }

    this.dispatch("error", { detail: { message } })
  }
}
