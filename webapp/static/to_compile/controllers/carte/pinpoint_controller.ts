import { Controller } from "@hotwired/stimulus"

class PinpointController extends Controller<HTMLElement> {
  static ACTIVE_PINPOINT_CLASSNAME = "active-pinpoint"

  static clearActivePinpoints() {
    document
      .querySelectorAll(`.${this.ACTIVE_PINPOINT_CLASSNAME}`)
      .forEach((element) => {
        element.classList.remove(this.ACTIVE_PINPOINT_CLASSNAME)
      })
  }

  setActive(event?: Event) {
    PinpointController.clearActivePinpoints()
    this.element.classList.add(PinpointController.ACTIVE_PINPOINT_CLASSNAME)
  }

  focus(e: CustomEvent) {
    // Per accessibility requirements, we need to focus on the last
    // opened pinpoint when we close an acteur details.
    const { acteurUuid } = e.detail
    const href = this.element.getAttribute("href")
    if (href?.includes(acteurUuid)) {
      this.element.focus()
    }
  }
}

export default PinpointController
