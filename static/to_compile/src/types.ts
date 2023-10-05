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
    id: number
    location: ActorLocation
    render_as_card: string
    actions: Action[]
    acteur_selected_action: Action

    constructor(actor_fields: object) {
        this.id = actor_fields["id"]
        this.location = actor_fields["location"]
        this.render_as_card = actor_fields["render_as_card"]
        this.actions = actor_fields["actions"]
        this.acteur_selected_action = actor_fields["acteur_selected_action"]
    }
}

export class SSCatObject {
    label: string
    sub_label: string
    identifier: int
}
