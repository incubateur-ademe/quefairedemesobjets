import { Controller } from "@hotwired/stimulus"
import { postSuggestion } from "./suggestion_post"

export default class extends Controller<HTMLElement> {
  static values = {
    action: String,
    statusUrl: String,
  }

  declare readonly actionValue: string
  declare readonly statusUrlValue: string

  update() {
    if (!this.actionValue || !this.statusUrlValue) {
      console.error("Action ou URL manquante")
      return
    }
    /*
  We need to create a form on the fly because the html fragment is already included in a form
  to manage checkboxes of the admin list view
  */
    const formData = new FormData()
    formData.append("action", this.actionValue)
    postSuggestion(this.statusUrlValue, formData)
  }
}
