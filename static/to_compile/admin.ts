// Styles pour l'admin (incluant Tailwind)
import "./styles/admin.css"

// Stimulus et Turbo
import { Application } from "@hotwired/stimulus"
import * as Turbo from "@hotwired/turbo"

import SuggestionGroupeRowController from "./controllers/admin/suggestion_groupe_row_controller"
import MapController from "./controllers/carte/map_controller"

window.stimulus = Application.start()

stimulus.register("suggestion-groupe-row", SuggestionGroupeRowController)
stimulus.register("map", MapController)

Turbo.session.drive = false

document.addEventListener("DOMContentLoaded", () => {
  stimulus.debug = document.body.dataset.stimulusDebug
})
