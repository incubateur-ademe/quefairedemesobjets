import { Application } from "@hotwired/stimulus"
import * as Turbo from "@hotwired/turbo"

import CarteController from "../../controllers/assistant/carte_controller"
import ChronoController from "../../controllers/assistant/chrono_controller"
import ComboboxController from "../../controllers/assistant/combobox_controller"
import CompteurController from "../../controllers/assistant/compteur_controller"
import PrefetchController from "../../controllers/assistant/prefetch_controller"
import SubmitController from "../../controllers/assistant/submit_controller"

// Stimulus application of the assistant V2, distinct from the site's own.
//
// The two must never run on the same document: each would scan the whole DOM
// and register its controllers, and a `data-controller` would be served
// twice. The lookbook picks the stack to load through the preview's `assets`
// attribute.
const application = Application.start()
application.register("assistant-carte", CarteController)
application.register("assistant-chrono", ChronoController)
application.register("assistant-combobox", ComboboxController)
application.register("assistant-compteur", CompteurController)
application.register("assistant-prefetch", PrefetchController)
application.register("assistant-submit", SubmitController)

// Turbo Drive is on: every screen change is a body swap, with view
// transitions and prefetch for free. The assistant lives in an iframe, but
// Drive only drives the iframe's own document, never the host page.
Turbo.session.drive = true

application.debug = Boolean(document.documentElement.dataset.stimulusDebug)

export default application
