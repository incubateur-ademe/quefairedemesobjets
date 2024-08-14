import { Controller } from "@hotwired/stimulus"
import { InteractionType, PosthogEventType } from "./types"
import posthog from "posthog-js"

export default class extends Controller<HTMLElement> {
    posthogWrapper(
        posthogEvent: PosthogEventType,
        specificInteractionType?: InteractionType,
    ) {
        console.debug("posthogWrapper", { posthogEvent, specificInteractionType })
        posthog.capture(posthogEvent, {
            specific_interaction_type: specificInteractionType,
        })
    }

    captureInteractionWithASolution() {
        this.posthogWrapper("interaction_with_a_solution")
    }

    captureInteractionWithMap() {
        this.posthogWrapper("interaction_with_a_solution", "with_map")
    }
}
