import "./styles/qfdmd.css"
import '@iframe-resizer/child'

// QFDMO
import "./js/carte"

// QFDMD
import SearchController from "./controllers/assistant/search"
import BlinkController from "./controllers/assistant/blink"
import AnalyticsController from "./controllers/assistant/analytics"

stimulus.debug = document.body.dataset.stimulusDebug
stimulus.register("search", SearchController)
stimulus.register("blink", BlinkController)
stimulus.register("analytics", AnalyticsController)

