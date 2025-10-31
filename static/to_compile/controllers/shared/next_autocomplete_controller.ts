import { Controller } from "@hotwired/stimulus"

export default abstract class extends Controller<HTMLElement> {
  static targets = ["results"]
  static values = {
    endpointUrl: String,
  }
  declare readonly resultsTarget: HTMLElement
  declare readonly endpointUrlValue: string

  connect() {
    console.log("coucou")
  }

  search(event) {
    const query = event.target.value
    const nextUrl = new URL(this.endpointUrlValue, window.location.origin)
    nextUrl.searchParams.set("q", query)
    this.resultsTarget.setAttribute("src", nextUrl.toString())
  }
}
