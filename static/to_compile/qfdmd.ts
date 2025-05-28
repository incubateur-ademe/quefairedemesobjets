import "./styles/qfdmd.css"
import '@iframe-resizer/child'

// QFDMD
import SearchController from "./controllers/assistant/search"
import BlinkController from "./controllers/assistant/blink"
import AnalyticsController from "./controllers/assistant/analytics"
import StateController from "./controllers/assistant/state"

// QFDMO
import "./js/carte"


stimulus.debug = document.body.dataset.stimulusDebug
stimulus.register("search", SearchController)
stimulus.register("blink", BlinkController)
stimulus.register("analytics", AnalyticsController)
stimulus.register("state", StateController)

