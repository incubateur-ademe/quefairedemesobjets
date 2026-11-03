import { Application } from "@hotwired/stimulus"

import ComboboxController from "../../controllers/assistant/combobox_controller"

// Distinct from the site's Stimulus application: the two must never run on
// the same document, or every `data-controller` would be served twice.
const application = Application.start()
application.register("assistant-combobox", ComboboxController)

application.debug = Boolean(document.documentElement.dataset.stimulusDebug)
