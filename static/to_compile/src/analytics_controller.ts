import { Controller } from "@hotwired/stimulus"
import { InteractionDetails, InteractionType } from "./types"
import posthog from "posthog-js"

export default class extends Controller<HTMLElement> {
    // Ci-dessous sont définis les événements utilisés côté métier
    // pour tracker l'activié des utilisteurs dans PostHog.
    //
    // Cette abstraction a été définie pour faciliter un éventuel changement d'outil futur.
    // Elle consiste simplement en :
    // - Une fonction nommée (en camelCase)
    // - Un appel à la méthode posthog.capture reprenant le nom de cette fonction dans la convention de nommage (snake_case)
    //
    // Il est important de ne pas intégrer trop de logique dans celle-ci, et de la conserver
    // dans les contrôleurs Stimulus.
    captureInteractionWithASolution(
        specificInteractionType?: InteractionType,
    ) {
        posthog.capture("interaction_with_a_solution", {
            specific_interaction_type: specificInteractionType,
        })
    }
}
