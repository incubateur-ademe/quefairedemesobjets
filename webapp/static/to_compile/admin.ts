// Styles pour l'admin (incluant Tailwind)
import "./styles/admin.css"

// Stimulus et Turbo
import { Application } from "@hotwired/stimulus"
import * as Turbo from "@hotwired/turbo"

import AnnuaireEntrepriseController from "./controllers/admin/annuaire_entreprise_controller"
import CellEditController from "./controllers/admin/cell_edit_controller"
import ReportUpdateController from "./controllers/admin/report_update_controller"
import SuggestionStatusController from "./controllers/admin/suggestion_status_controller"
import SuggestionMapUpdateController from "./controllers/admin/suggestion_map_update_controller"
import MapSearchController from "./controllers/admin/map_search_controller"
import MapController from "./controllers/carte/map_controller"

window.stimulus = Application.start()

stimulus.register("annuaire-entreprise", AnnuaireEntrepriseController)
stimulus.register("cell-edit", CellEditController)
stimulus.register("report-update", ReportUpdateController)
stimulus.register("suggestion-status", SuggestionStatusController)
stimulus.register("suggestion-map-update", SuggestionMapUpdateController)
stimulus.register("map-search", MapSearchController)
stimulus.register("map", MapController)

Turbo.session.drive = false

document.addEventListener("DOMContentLoaded", () => {
  stimulus.debug = document.body.dataset.stimulusDebug
})
