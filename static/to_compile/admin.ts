// Styles pour l'admin (incluant Tailwind)
import "./styles/admin.css"

// Stimulus et Turbo
import { Application } from "@hotwired/stimulus"
import * as Turbo from "@hotwired/turbo"

// TODO : import here  the stimulus controllers
// import AdminCategorieWidgetController from "./controllers/admin/categorie_widget_controller"

window.stimulus = Application.start()

// TODO : register here the stimulus controllers
// stimulus.register("admin-categorie-widget", AdminCategorieWidgetController)

Turbo.session.drive = false

document.addEventListener("DOMContentLoaded", () => {
  stimulus.debug = document.body.dataset.stimulusDebug
})
