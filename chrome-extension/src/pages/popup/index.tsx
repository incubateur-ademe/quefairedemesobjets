import React from "react"
import { createRoot } from "react-dom/client"
import { startReactDsfr } from "@codegouvfr/react-dsfr/spa"
import "@codegouvfr/react-dsfr/main.css"
import "@pages/popup/index.css"
import Popup from "./Popup"

startReactDsfr({ defaultColorScheme: "light" })

function init() {
  const rootContainer = document.querySelector("#__root")
  if (!rootContainer) throw new Error("Can't find Popup root element")
  const root = createRoot(rootContainer)
  root.render(<Popup />)
}

init()
