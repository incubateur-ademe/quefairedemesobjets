import { Application } from "@hotwired/stimulus"

import AutocompleteController from "../src/autocomplete_controller"
import MapController from "../src/map_controller"

window.stimulus = Application.start()
stimulus.register("map", MapController)
stimulus.register("autocomplete", AutocompleteController)
