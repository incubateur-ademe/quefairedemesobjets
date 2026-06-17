// Entry point for the cohorte review screen (data:cohorte_review).
// Mixed-style screen: the chrome (view switch, toolbar, bulkbar, dialogs,
// pagination) is Shoelace + bespoke CSS, while the « vue par acteurs » card
// bodies are the server-rendered DSFR/Tailwind (qf-*) partial. To render
// those bodies correctly the standalone page must also load the DSFR styles
// and the Tailwind utilities (qfdmo.css carries both fr-table and qf-*).
import "@shoelace-style/shoelace/dist/themes/light.css"
import "./styles/qfdmo.css"
import "./styles/cohorte-review.css"

import "@shoelace-style/shoelace/dist/components/badge/badge.js"
import "@shoelace-style/shoelace/dist/components/button/button.js"
import "@shoelace-style/shoelace/dist/components/checkbox/checkbox.js"
import "@shoelace-style/shoelace/dist/components/dialog/dialog.js"
import "@shoelace-style/shoelace/dist/components/drawer/drawer.js"
import "@shoelace-style/shoelace/dist/components/input/input.js"
import "@shoelace-style/shoelace/dist/components/option/option.js"
import "@shoelace-style/shoelace/dist/components/radio-button/radio-button.js"
import "@shoelace-style/shoelace/dist/components/radio-group/radio-group.js"
import "@shoelace-style/shoelace/dist/components/select/select.js"
import "@shoelace-style/shoelace/dist/components/textarea/textarea.js"

import { Application } from "@hotwired/stimulus"

import CohorteReviewController from "./controllers/admin/cohorte_review_controller"
// Controllers needed by the server-rendered card bodies (vue par acteurs)
// and the localisation map dialog. Same set the Django admin registers.
import CellEditController from "./controllers/admin/cell_edit_controller"
import ReportUpdateController from "./controllers/admin/report_update_controller"
import SuggestionStatusController from "./controllers/admin/suggestion_status_controller"
import SuggestionMapUpdateController from "./controllers/admin/suggestion_map_update_controller"
import MapController from "./controllers/carte/map_controller"

const application = Application.start()
application.register("cohorte-review", CohorteReviewController)
application.register("cell-edit", CellEditController)
application.register("report-update", ReportUpdateController)
application.register("suggestion-status", SuggestionStatusController)
application.register("suggestion-map-update", SuggestionMapUpdateController)
application.register("map", MapController)
