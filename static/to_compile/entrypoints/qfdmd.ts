import * as Turbo from "@hotwired/turbo"
import { Application } from "@hotwired/stimulus"
import '@iframe-resizer/child'

// QFDMD
import SearchController from "../js/controllers/assistant/search"
import BlinkController from "../js/controllers/assistant/blink"
import AnalyticsController from "../js/controllers/assistant/analytics"
import CopyController from "../js/copy_controller"

// QFDMO
import AddressAutocompleteController from "../js/address_autocomplete_controller"
import GenericAutocompleteController from "../js/generic_autocomplete_controller"
import MapController from "../js/map_controller"
import ScrollController from "../js/scroll_controller"
import SearchSolutionFormController from "../js/search_solution_form_controller"
import SsCatObjectAutocompleteController from "../js/ss_cat_object_autocomplete_controller"

import "../js/browser_check"
import "../js/iframe"

window.stimulus = Application.start()
stimulus.debug = document.body.dataset.stimulusDebug
stimulus.register("search", SearchController)
stimulus.register("blink", BlinkController)
stimulus.register("copy", CopyController)
stimulus.register("analytics", AnalyticsController)

stimulus.register("map", MapController)
stimulus.register("ss-cat-object-autocomplete", SsCatObjectAutocompleteController)
stimulus.register("address-autocomplete", AddressAutocompleteController)
stimulus.register("search-solution-form", SearchSolutionFormController)
// stimulus.register("analytics", AnalyticsController)
stimulus.register("autocomplete", GenericAutocompleteController)
stimulus.register("copy", CopyController)
stimulus.register("scroll", ScrollController)

Turbo.session.drive = false;
