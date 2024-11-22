import * as Turbo from "@hotwired/turbo"
import { Application } from "@hotwired/stimulus"

import SearchController from "../js/controllers/assistant/search"

window.stimulus = Application.start()
stimulus.register("search", SearchController)

// TODO: remove once the map will be loaded using a turbo frame
window.addEventListener("load", () => {
  const iframe = document.querySelector("#ou-l-apporter iframe")
  iframe.contentWindow.postMessage("ademe", "*");
})


Turbo.session.drive = false;
