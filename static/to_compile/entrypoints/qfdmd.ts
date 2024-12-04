import * as Turbo from "@hotwired/turbo"
import 'iframe-resizer/js/iframeResizer.contentWindow.min.js';
import { Application } from "@hotwired/stimulus"

import SearchController from "../js/controllers/assistant/search"
import BlinkController from "../js/controllers/assistant/blink"
import CopyController from "../js/copy_controller"

window.stimulus = Application.start()
stimulus.register("search", SearchController)
stimulus.register("blink", BlinkController)
stimulus.register("copy", CopyController)


Turbo.session.drive = false;
