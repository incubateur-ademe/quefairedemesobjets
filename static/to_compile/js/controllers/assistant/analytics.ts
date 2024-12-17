import { Controller } from "@hotwired/stimulus"
import { InteractionType as PosthogUIInteractionType, PosthogEventType } from "./types"
import posthog from "posthog-js"

const posthogConfig = {
  api_host: "https://eu.posthog.com",
  autocapture: false,
  persistence: "memory",
}

export default class extends Controller<HTMLElement> {
  declare readonly posthogKeyValue
  declare readonly posthogDebugValue
  declare readonly userUsername
  declare readonly userEmail
  declare readonly userAdmin

  static values= {
    posthogKey: String,
    posthogDebug: Boolean,
    userUsername: String,
    userEmail: String,
    userAdmin: Boolean
  }

  initialize(): void {
    posthog.init("phc_SGbYOrenShCMKJOQYyl62se9ZqCHntjTlzgKNhrKnzm", posthogConfig) // pragma: allowlist secret

    // pageview
    // identify
    // intersection observer
    // exclude team visits
      if (this.userUsername) {

      posthog.identify(this.userUsername, {
        email: this.userEmail,
        admin: this.userAdmin,
        iframe: this.#areWeInAnIframe(),
      })
    }
  }

  #areWeInAnIframe() {
    try {
        if (window.self !== window.top) {
            return true
        }
    } catch (e) {
        // Unable to access window.top
        // this might be due to cross-origin restrictions.
        // Assuming it's inside an iframe.
        return true
    }

    if (document.referrer) {
      return true
    }
    return false
  }
    // Sert principalement à typer les appels à la méthode capture de Posthog.
    // Ça évite d'appeler un événement indéfini, ce qui peut rapidement polluer
    // les données stockées côtés PostHog.
    capture(posthogEvent: PosthogEventType, details: object) {
        posthog.capture(posthogEvent, details)
    }

    captureUIInteraction(UIInteractionType: PosthogUIInteractionType) {
        this.capture("ui_interaction", {
            ui_interaction_type: UIInteractionType,
        })
    }

    captureInteractionWithSolutionDetails() {
        this.captureUIInteraction("solution_details")
    }

    captureInteractionWithMap() {
        this.captureUIInteraction("map")
    }
}
