import { Controller } from "@hotwired/stimulus";
import { ReemploiActeurMap } from "./reemploi_acteur_map";

export default class extends Controller<HTMLElement> {
    static targets = ["reemploiacteur"];
    readonly reemploiacteurTargets: Array<HTMLScriptElement>

    static values = {location: {type: Object, default: {}}}
    readonly locationValue: object

    initialize() {
        new ReemploiActeurMap({
            location: this.locationValue,
            reemploiacteurs: this.reemploiacteurTargets
        })
    }
}

