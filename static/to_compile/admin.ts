// Styles pour l'admin (incluant Tailwind)
import "./styles/admin.css"

// Stimulus et Turbo
import { Application } from "@hotwired/stimulus"
import * as Turbo from "@hotwired/turbo"

// TODO : import here  the stimulus controllers
import SuggestionGroupeRowController from "./controllers/admin/suggestion_groupe_row_controller"

window.stimulus = Application.start()

// TODO : register here the stimulus controllers
stimulus.register("suggestion-groupe-row", SuggestionGroupeRowController)

Turbo.session.drive = false

document.addEventListener("DOMContentLoaded", () => {
  stimulus.debug = document.body.dataset.stimulusDebug
})
