export interface Location {
    latitude?: number
    longitude?: number
}

export interface ActorLocation {
    coordinates: number[]
}
export interface Action {
    couleur: string
    icon: string
}

export class Actor {
    identifiant_unique: string
    location: ActorLocation
    actions: Action[]
    acteur_selected_action: Action

    constructor(actor_fields: object) {
        this.identifiant_unique = actor_fields["identifiant_unique"]
        this.location = actor_fields["location"]
        this.actions = actor_fields["actions"]
        this.acteur_selected_action = actor_fields["acteur_selected_action"]
    }
}

export class SSCatObject {
    label: string
    sub_label: string
    identifier: int
}
