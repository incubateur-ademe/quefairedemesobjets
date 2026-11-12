import "./styles/assistant.css"

// Child half of iframe-resizer: the host page's iframe.js runs the parent half.
import "@iframe-resizer/child"
import posthog from "posthog-js"

import "./js/assistant/application"

// iframe-resizer observes the <body> found at startup, but Turbo Drive swaps
// the body on every visit: observe the current one instead.
const bodyObserver = new ResizeObserver(() => window.parentIFrame?.resize())
let isFirstLoad = true

document.addEventListener("turbo:load", () => {
  bodyObserver.disconnect()
  bodyObserver.observe(document.body)
  if (!isFirstLoad) {
    window.parentIFrame?.scrollToOffset(0, 0)
    // PostHog only captures the pageview of the initial load.
    posthog.capture("$pageview")
  }
  isFirstLoad = false
})
