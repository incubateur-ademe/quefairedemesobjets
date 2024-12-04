import * as Turbo from "@hotwired/turbo"
import { Application } from "@hotwired/stimulus"

import SearchController from "../js/controllers/assistant/search"
import BlinkController from "../js/controllers/assistant/blink"

window.stimulus = Application.start()
stimulus.register("search", SearchController)
stimulus.register("blink", BlinkController)


Turbo.session.drive = false;
