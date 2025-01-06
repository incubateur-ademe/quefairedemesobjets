import * as Turbo from "@hotwired/turbo"
import 'iframe-resizer/js/iframeResizer.contentWindow.min.js';
import { Application } from "@hotwired/stimulus"

import SearchController from "../js/controllers/assistant/search"
import BlinkController from "../js/controllers/assistant/blink"
import AnalyticsController from "../js/controllers/assistant/analytics"
import CopyController from "../js/copy_controller"

window.stimulus = Application.start()
stimulus.debug = document.body.dataset.stimulusDebug
stimulus.register("search", SearchController)
stimulus.register("blink", BlinkController)
stimulus.register("copy", CopyController)
stimulus.register("analytics", AnalyticsController)


Turbo.session.drive = false;
