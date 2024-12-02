import { Application } from "@hotwired/stimulus"
import AdminCategorieWidgetController from "../js/controllers/admin/categorie_widget_controller"

window.stimulus = Application.start()
stimulus.register("admin-categorie-widget", AdminCategorieWidgetController)
