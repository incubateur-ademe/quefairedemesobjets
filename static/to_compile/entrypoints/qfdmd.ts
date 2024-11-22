import * as Turbo from "@hotwired/turbo"
import { Application } from "@hotwired/stimulus"

import SearchController from "../js/controllers/assistant/search"

window.stimulus = Application.start()
stimulus.register("search", SearchController)

Turbo.session.drive = false;
