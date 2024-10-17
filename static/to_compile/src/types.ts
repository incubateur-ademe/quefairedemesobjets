export interface Location {
    latitude?: number
    longitude?: number
}

export interface ActorLocation {
    coordinates: number[]
}

export interface DisplayedActeur {
  identifiant_unique: string
  icon: string
  couleur: string
  location: ActorLocation
  bonus: boolean
}

export class SSCatObject {
    label: string
    sub_label: string
    identifier: number
}

export type InteractionType = "map" | "solution_details"
export type PosthogEventType = "ui_interaction"
