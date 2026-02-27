import {
  CONVERSION_SCORE_KEYS as _CONVERSION_SCORE_KEYS,
  IFRAME_REFERRER_SESSION_KEY as _IFRAME_REFERRER_SESSION_KEY,
  LOCATION_SESSION_KEYS as _LOCATION_SESSION_KEYS,
} from "../../shared/constants";

// Re-export shared detection types
export type {
  DetectedIframe,
  DetectionConfig,
  IframeType,
} from "../../shared/detection";
export type { IntegrationWarning as Warning } from "../../shared/detection";

// Re-export shared constants
export {
  CARTE_ROUTE,
  CARTE_SCRIPT_FILENAME,
  CONVERSION_SCORE_KEYS,
  DECHET_ROUTE,
  FORMULAIRE_ROUTE,
  FORMULAIRE_SCRIPT_FILENAME,
  IFRAME_REFERRER_SESSION_KEY,
  KNOWN_DOMAINS,
  LOCATION_SESSION_KEYS,
  MAIN_DOMAIN,
  USER_CONVERSION_SCORE_CONFIG,
} from "../../shared/constants";
export type { UserConversionConfig } from "../../shared/constants";

// Re-export shared detection functions
export {
  buildDetectionConfig,
  detectIframeIntegrations,
} from "../../shared/detection";

// -- Chrome-extension-specific types --

export interface SessionStorageData {
  // Location
  adresse: string | null;
  latitude: string | null;
  longitude: string | null;
  // Conversion score
  homePageView: string | null;
  produitPageView: string | null;
  userInteractionWithMap: string | null;
  userInteractionWithSolutionDetails: string | null;
  // Iframe referrer
  qf_ifr: string | null;
}

export const SESSION_STORAGE_KEYS: (keyof SessionStorageData)[] = [
  ..._LOCATION_SESSION_KEYS,
  ..._CONVERSION_SCORE_KEYS,
  _IFRAME_REFERRER_SESSION_KEY,
] as (keyof SessionStorageData)[];

export interface PageAnalysis {
  iframes: import("../../shared/detection").DetectedIframe[];
  totalWarnings: number;
  sessionStorage: SessionStorageData | null;
  isQfdmoPage: boolean;
}
