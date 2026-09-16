import { Application } from "@hotwired/stimulus"

import CarteController from "../../controllers/assistant/carte_controller"
import ChronoController from "../../controllers/assistant/chrono_controller"

// Stimulus application of the assistant V2, distinct from the site's own.
//
// The two must never run on the same document: each would scan the whole DOM
// and register its controllers, and a `data-controller` would be served
// twice. The lookbook picks the stack to load through the preview's `assets`
// attribute.
const application = Application.start()
application.register("assistant-carte", CarteController)
application.register("assistant-chrono", ChronoController)

application.debug = Boolean(document.documentElement.dataset.stimulusDebug)

export default application
