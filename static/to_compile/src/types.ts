export interface Location {
    latitude?: number
    longitude?: number
}

export interface ActorLocation {
    coordinates: number[]
}

export class Actor {
    identifiant_unique: string
    location: ActorLocation
    icon: string
    couleur: string

    constructor(actor_fields: object) {
        this.identifiant_unique = actor_fields["identifiant_unique"]
        this.location = actor_fields["location"]
        this.icon = actor_fields["icon"]
        this.couleur = actor_fields["couleur"]
    }
}

export class SSCatObject {
    label: string
    sub_label: string
    identifier: int
}

export type InteractionType = "with_map"
export type PosthogEventType = "interaction_with_a_solution"
