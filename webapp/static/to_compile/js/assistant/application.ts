import { Application } from "@hotwired/stimulus"
import "@hotwired/turbo"

import CarteController from "../../controllers/assistant/carte_controller"
import ChronoController from "../../controllers/assistant/chrono_controller"
import ComboboxController from "../../controllers/assistant/combobox_controller"
import PrefetchController from "../../controllers/assistant/prefetch_controller"
import SubmitController from "../../controllers/assistant/submit_controller"

// Distinct from the site's Stimulus application: the two must never run on
// the same document, or every `data-controller` would be served twice.
const application = Application.start()
application.register("assistant-carte", CarteController)
application.register("assistant-chrono", ChronoController)
application.register("assistant-combobox", ComboboxController)
application.register("assistant-prefetch", PrefetchController)
application.register("assistant-submit", SubmitController)

application.debug = document.documentElement.dataset.stimulusDebug === "true"
