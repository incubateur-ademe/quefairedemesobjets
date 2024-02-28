import "@gouvfr/dsfr/dist/dsfr.module.js"
import { Application } from "@hotwired/stimulus"
import * as Turbo from "@hotwired/turbo"

import AddressAutocompleteController from "../src/address_autocomplete_controller"
import DisplaySolutionController from "../src/display_solutions_controller"
import MapController from "../src/map_controller"
import SearchSolutionFormController from "../src/search_solution_form_controller"
import SsCatObjectAutocompleteController from "../src/ss_cat_object_autocomplete_controller"

import "../src/browser_check"

window.stimulus = Application.start()
stimulus.register("map", MapController)
stimulus.register("ss-cat-object-autocomplete", SsCatObjectAutocompleteController)
stimulus.register("address-autocomplete", AddressAutocompleteController)
stimulus.register("search-solution-form", SearchSolutionFormController)
stimulus.register("display-solutions", DisplaySolutionController)

Turbo.session.drive = false
