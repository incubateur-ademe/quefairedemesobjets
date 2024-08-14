import { Controller } from "@hotwired/stimulus"
import { InteractionType as PosthogUIInteractionType, PosthogEventType } from "./types"
import posthog from "posthog-js"

export default class extends Controller<HTMLElement> {
    // Sert principalement à type les appels à la   this.capturede Posthog.
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
