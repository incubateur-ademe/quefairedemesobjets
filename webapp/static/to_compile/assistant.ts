import "./styles/assistant.css"

// Third-party scripts
// The host page's iframe.js initializes the parent half of iframe-resizer
// (ADR 0013) : without the child half, the iframe keeps its default height.
import "@iframe-resizer/child"

import "./js/assistant/application"
