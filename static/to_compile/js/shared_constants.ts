/**
 * Shared constants used across the main project and the chrome extension.
 * This is the single source of truth for domains, routes, session storage keys,
 * and conversion score configuration.
 */

// -- Domains --

export const KNOWN_DOMAINS = [
  "quefairedemesobjets.fr",
  "quefairedemesobjets.ademe.fr",
  "quefairedemesdechets.ademe.fr",
] as const

export const MAIN_DOMAIN = "quefairedemesdechets.ademe.fr"

// -- Iframe script filenames (as served by Django) --

export const CARTE_SCRIPT_FILENAME = "carte.js"
export const FORMULAIRE_SCRIPT_FILENAME = "iframe.js"

// -- Route paths --

export const CARTE_ROUTE = "carte"
export const FORMULAIRE_ROUTE = "formulaire"
// The deployed version of quefairedemesdechets uses "dechet" as the assistant route
export const DECHET_ROUTE = "dechet"

// -- Session storage keys --

export const IFRAME_REFERRER_SESSION_KEY = "qf_ifr"

export const LOCATION_SESSION_KEYS = ["adresse", "latitude", "longitude"] as const

// -- Conversion score --

export type UserConversionConfig = {
  homePageView: number
  produitPageView: number
  userInteractionWithMap: number
  userInteractionWithSolutionDetails: number
}

export const USER_CONVERSION_SCORE_CONFIG: UserConversionConfig = {
  homePageView: 0,
  produitPageView: 1,
  userInteractionWithMap: 1,
  userInteractionWithSolutionDetails: 1,
}

export const CONVERSION_SCORE_KEYS = Object.keys(
  USER_CONVERSION_SCORE_CONFIG,
) as (keyof UserConversionConfig)[]
