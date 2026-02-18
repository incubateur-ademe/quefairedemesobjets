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

  setActive(event: Event) {
    PinpointController.clearActivePinpoints()
    this.element.classList.add(PinpointController.ACTIVE_PINPOINT_CLASSNAME)
  }
}

export default PinpointController
