/**
 * Shared constants used across webapp, chrome extension, and scripts.
 * This is the single source of truth for domains, routes, and script filenames.
 *
 * Session storage and conversion score constants are defined in
 * webapp/static/to_compile/js/constants.ts and re-exported here.
 */

// -- Domains --

export const KNOWN_DOMAINS = [
  "quefairedemesobjets.fr",
  "quefairedemesobjets.ademe.fr",
  "quefairedemesdechets.ademe.fr",
  "lvao.ademe.fr",
] as const;

export const MAIN_DOMAIN = "quefairedemesdechets.ademe.fr";

// -- Iframe script filenames (as served by Django) --

export const CARTE_SCRIPT_FILENAME = "carte.js";
export const FORMULAIRE_SCRIPT_FILENAME = "iframe.js";

// -- Route paths --

export const CARTE_ROUTE = "carte";
export const FORMULAIRE_ROUTE = "formulaire";
// The deployed version of quefairedemesdechets uses "dechet" as the assistant route
export const DECHET_ROUTE = "dechet";

// -- Re-export webapp constants (session storage, conversion score) --

export {
  IFRAME_REFERRER_SESSION_KEY,
  LOCATION_SESSION_KEYS,
  USER_CONVERSION_SCORE_CONFIG,
  CONVERSION_SCORE_KEYS,
} from "../../webapp/static/to_compile/js/constants";
export type { UserConversionConfig } from "../../webapp/static/to_compile/js/constants";
