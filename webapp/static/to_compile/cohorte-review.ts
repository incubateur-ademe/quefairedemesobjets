// Entry point for the cohorte review screen (data:cohorte_review).
// Deliberately standalone: no DSFR, no Turbo — Shoelace components +
// a single Stimulus controller hosting TanStack Table.
import "@shoelace-style/shoelace/dist/themes/light.css"
import "./styles/cohorte-review.css"

import "@shoelace-style/shoelace/dist/components/badge/badge.js"
import "@shoelace-style/shoelace/dist/components/button/button.js"
import "@shoelace-style/shoelace/dist/components/checkbox/checkbox.js"

import { Application } from "@hotwired/stimulus"

import CohorteReviewController from "./controllers/admin/cohorte_review_controller"

const application = Application.start()
application.register("cohorte-review", CohorteReviewController)
