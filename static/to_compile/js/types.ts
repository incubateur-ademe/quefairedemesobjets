import type { EventName } from "posthog-js"

export interface Location {
  latitude?: number
  longitude?: number
}

export interface ActorLocation {
  coordinates: number[]
}

export interface DisplayedActeur {
  fillBackground: boolean
  uuid: string
  icon: string
  iconFile: string
  couleur: string
  location: ActorLocation
  bonus: boolean
  reparer: boolean
}

export class SSCatObject {
  label: string
  sub_label: string
  identifier: number
}

export type InteractionType = "solution_details" | "map"
export type PosthogEventType = "ui_interaction" | EventName
