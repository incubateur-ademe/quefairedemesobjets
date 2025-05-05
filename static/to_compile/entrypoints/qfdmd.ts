import '@iframe-resizer/child'
import "./qfdmo"

// QFDMD
import SearchController from "../js/controllers/assistant/search"
import BlinkController from "../js/controllers/assistant/blink"
import AnalyticsController from "../js/controllers/assistant/analytics"
import CopyController from "../js/copy_controller"

// Handled by qfdmo.ts
// window.stimulus = Application.start()
stimulus.debug = document.body.dataset.stimulusDebug
stimulus.register("search", SearchController)
stimulus.register("blink", BlinkController)
stimulus.register("copy", CopyController)
stimulus.register("analytics", AnalyticsController)

// Handle by qfdmo
// Turbo.session.drive = false;
