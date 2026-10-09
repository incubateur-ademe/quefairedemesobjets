import "@awesome.me/webawesome/dist/styles/webawesome.css"
import "@awesome.me/webawesome/dist/translations/fr.js"
import "./styles/revue.css"

import { StrictMode } from "react"
import { createRoot } from "react-dom/client"

import { App } from "./App"
import { readBootstrap } from "./bootstrap"
import { registerIcons } from "./icons"

registerIcons()

const bootstrap = readBootstrap()
document.documentElement.lang = "fr"

createRoot(document.getElementById("revue-root")!).render(
  <StrictMode>
    <App bootstrap={bootstrap} />
  </StrictMode>,
)
