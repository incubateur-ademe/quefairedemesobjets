import { Application } from "@hotwired/stimulus"

import CarteController from "../../controllers/assistant/carte_controller"
import ChronoController from "../../controllers/assistant/chrono_controller"

// Application Stimulus propre à l'assistant V2, distincte de celle du site.
//
// Les deux ne doivent jamais tourner sur le même document : chacune scannerait
// tout le DOM et enregistrerait ses contrôleurs, et un `data-controller`
// serait servi deux fois. C'est le lookbook qui choisit la pile à charger,
// via l'attribut `assets` de la preview.
const application = Application.start()
application.register("assistant-carte", CarteController)
application.register("assistant-chrono", ChronoController)

application.debug = Boolean(document.documentElement.dataset.stimulusDebug)

export default application
