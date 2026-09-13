import { Application } from "@hotwired/stimulus"
import * as Turbo from "@hotwired/turbo"

import CarteController from "../../controllers/assistant/carte_controller"
import ChronoController from "../../controllers/assistant/chrono_controller"
import ComboboxController from "../../controllers/assistant/combobox_controller"

const application = Application.start()
application.register("assistant-carte", CarteController)
application.register("assistant-chrono", ChronoController)
application.register("assistant-combobox", ComboboxController)

// L'assistant vit en iframe : prendre le contrôle de la navigation du document
// hôte via Turbo Drive n'aurait pas de sens.
Turbo.session.drive = false

application.debug = Boolean(document.documentElement.dataset.stimulusDebug)

export default application
