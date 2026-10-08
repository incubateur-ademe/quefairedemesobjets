import "./styles/assistant.css"

// Third-party scripts
// The host page's iframe.js initializes the parent half of iframe-resizer
// (ADR 0013) : without the child half, the iframe keeps its default height.
import "@iframe-resizer/child"

import "./js/assistant/application"

// iframe-resizer observes the <body> it found at startup, but Turbo Drive
// swaps the body on every visit: left alone, the iframe would stop following
// its content after the first screen. The current body is observed instead,
// and reports its size.
const bodyObserver = new ResizeObserver(() => window.parentIFrame?.resize())
let isFirstLoad = true

document.addEventListener("turbo:load", () => {
  bodyObserver.disconnect()
  bodyObserver.observe(document.body)
  // A new screen starts at its top: otherwise the host page stays where the
  // click happened, possibly below the top of a shorter screen.
  if (!isFirstLoad) window.parentIFrame?.scrollToOffset(0, 0)
  isFirstLoad = false
})
