import { Controller } from "@hotwired/stimulus"
import { InteractionType as PosthogUIInteractionType, PosthogEventType } from "./types"
import posthog from "posthog-js"

export default class extends Controller<HTMLElement> {
    posthogCapture(
        posthogEvent: PosthogEventType,
        uiInteractionType?: PosthogUIInteractionType,
    ) {
        posthog.capture(posthogEvent, {
            ui_interaction_type: uiInteractionType,
        })
    }

    captureInteractioncaptureInteractionWithSolutionDetailsDetails() {
        this.posthogCapture("ui_interaction", "solution_details")
    }

    captureInteractionWithMap() {
        this.posthogCapture("ui_interaction", "map")
    }
}
