import "@gouvfr/dsfr/dist/dsfr.nomodule.js"
import { Application } from "@hotwired/stimulus"

import AddressAutocompleteController from "../src/address_autocomplete_controller"
import AutocompleteController from "../src/autocomplete_controller"
import ChooseActionController from "../src/choose_action_controller"
import MapController from "../src/map_controller"

window.stimulus = Application.start()
stimulus.register("map", MapController)
stimulus.register("autocomplete", AutocompleteController)
stimulus.register("address-autocomplete", AddressAutocompleteController)
stimulus.register("choose-action", ChooseActionController)
