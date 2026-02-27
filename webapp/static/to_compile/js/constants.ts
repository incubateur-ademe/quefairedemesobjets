/**
 * Webapp-specific constants for session storage and conversion score.
 * Re-exported by shared/constants.ts for use by chrome-extension.
 */

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
