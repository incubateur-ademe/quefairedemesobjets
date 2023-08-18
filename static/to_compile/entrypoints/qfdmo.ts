import { Application } from "@hotwired/stimulus"

import MapController from "../src/map_controller"

window.stimulus = Application.start()
stimulus.register("map", MapController)
