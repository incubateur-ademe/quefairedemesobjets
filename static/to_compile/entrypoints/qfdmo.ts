import "@gouvfr/dsfr/dist/dsfr.module.js"
import { Application } from "@hotwired/stimulus"
import * as Turbo from "@hotwired/turbo"

import AddressAutocompleteController from "../src/address_autocomplete_controller"
import MapController from "../src/map_controller"
import GenericAutocompleteController from "../src/generic_autocomplete_controller"
import AnalyticsController from "../src/analytics_controller"
import SearchSolutionFormController from "../src/search_solution_form_controller"
import SsCatObjectAutocompleteController from "../src/ss_cat_object_autocomplete_controller"
import CopyController from "../src/copy_controller"

import "../src/browser_check"
import "../src/iframe"

window.stimulus = Application.start()
//  TODO : do not merge
window.stimulus.debug = true
stimulus.register("map", MapController)
stimulus.register("ss-cat-object-autocomplete", SsCatObjectAutocompleteController)
stimulus.register("address-autocomplete", AddressAutocompleteController)
stimulus.register("search-solution-form", SearchSolutionFormController)
stimulus.register("analytics", AnalyticsController)
stimulus.register("autocomplete", GenericAutocompleteController)
stimulus.register("copy", CopyController)
stimulus.register("scrollController", ScrollController)

Turbo.session.drive = false
