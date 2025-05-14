import { Application } from "@hotwired/stimulus"
import * as Turbo from "@hotwired/turbo"

import AnalyticsController from "../controllers/shared/analytics_controller"
import CopyController from "../controllers/shared/copy_controller"
import GenericAutocompleteController from "../controllers/shared/generic_autocomplete_controller"
import ScrollController from "../controllers/shared/scroll_controller"

import AddressAutocompleteController from "../controllers/carte/address_autocomplete_controller"
import MapController from "../controllers/carte/map_controller"
import SearchSolutionFormController from "../controllers/carte/search_solution_form_controller"
import SsCatObjectAutocompleteController from "../controllers/carte/ss_cat_object_autocomplete_controller"


window.stimulus = Application.start()
stimulus.register("map", MapController)
stimulus.register("ss-cat-object-autocomplete", SsCatObjectAutocompleteController)
stimulus.register("address-autocomplete", AddressAutocompleteController)
stimulus.register("search-solution-form", SearchSolutionFormController)
stimulus.register("analytics", AnalyticsController)
stimulus.register("autocomplete", GenericAutocompleteController)
stimulus.register("copy", CopyController)
stimulus.register("scroll", ScrollController)

Turbo.session.drive = false
