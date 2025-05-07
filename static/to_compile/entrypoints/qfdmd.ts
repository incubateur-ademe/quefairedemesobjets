import "../styles/qfdmo.css"

import '@iframe-resizer/child'

// QFDMO
import "./carte"

// QFDMD
import SearchController from "../controllers/assistant/search"
import BlinkController from "../controllers/assistant/blink"
import AnalyticsController from "../controllers/assistant/analytics"
import CopyController from "../controllers/shared/copy_controller"

// Handled by carte.ts
// window.stimulus = Application.start()
stimulus.debug = document.body.dataset.stimulusDebug
stimulus.register("search", SearchController)
stimulus.register("blink", BlinkController)
stimulus.register("copy", CopyController)
stimulus.register("analytics", AnalyticsController)

// Handle by carte.ts
// Turbo.session.drive = false;
