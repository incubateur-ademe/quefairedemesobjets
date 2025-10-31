import { Application } from "@hotwired/stimulus"
import * as Turbo from "@hotwired/turbo"

import CopyController from "../controllers/shared/copy_controller"
import GenericAutocompleteController from "../controllers/shared/generic_autocomplete_controller"
import ScrollController from "../controllers/shared/scroll_controller"

import AddressAutocompleteController from "../controllers/carte/address_autocomplete_controller"
import MapController from "../controllers/carte/map_controller"
import SearchSolutionFormController from "../controllers/carte/search_solution_form_controller"
import SsCatObjectAutocompleteController from "../controllers/carte/ss_cat_object_autocomplete_controller"
import ActeurDetailsController from "../controllers/carte/acteur_details"
import ModelAutocompleteController from "../controllers/shared/model_autocomplete_controller"

// QFDMD
import SearchController from "../controllers/assistant/search"
import BlinkController from "../controllers/assistant/blink"
import AnalyticsController from "../controllers/shared/analytics"
import StateController from "../controllers/assistant/state"

window.stimulus = Application.start()

stimulus.register("map", MapController)
stimulus.register("ss-cat-object-autocomplete", SsCatObjectAutocompleteController)
stimulus.register("address-autocomplete", AddressAutocompleteController)
stimulus.register("search-solution-form", SearchSolutionFormController)
stimulus.register("autocomplete", GenericAutocompleteController)
stimulus.register("copy", CopyController)
stimulus.register("scroll", ScrollController)
stimulus.register("acteur-details", ActeurDetailsController)
stimulus.register("model-autocomplete", ModelAutocompleteController)

stimulus.register("search", SearchController)
stimulus.register("blink", BlinkController)
stimulus.register("analytics", AnalyticsController)
stimulus.register("state", StateController)

Turbo.session.drive = false

document.addEventListener("DOMContentLoaded", () => {
  stimulus.debug = document.body.dataset.stimulusDebug
})
