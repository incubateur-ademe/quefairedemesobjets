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
    location: ActorLocation
    render_as_card: string
    actions: Action[]

    constructor(actor_fields: object) {
        this.location = actor_fields["location"]
        this.render_as_card = actor_fields["render_as_card"]
        this.actions = actor_fields["actions"]
    }
}
