import {
  CONVERSION_SCORE_KEYS as _CONVERSION_SCORE_KEYS,
  IFRAME_REFERRER_SESSION_KEY as _IFRAME_REFERRER_SESSION_KEY,
  LOCATION_SESSION_KEYS as _LOCATION_SESSION_KEYS,
} from "../../webapp/static/to_compile/js/shared_constants";

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
} from "../../webapp/static/to_compile/js/shared_constants";
export type { UserConversionConfig } from "../../webapp/static/to_compile/js/shared_constants";

export type IframeType =
  | "carte"
  | "carte_sur_mesure"
  | "carte_preconfiguree"
  | "assistant"
  | "unknown";

export interface DetectedIframe {
  src: string;
  domain: string;
  type: IframeType;
  slug?: string;
  hasAdjacentScript: boolean;
  scriptSrc?: string;
  scriptDataAttributes: Record<string, string>;
  iframeDataAttributes: Record<string, string>;
  hasIframeResizer: boolean;
  insideTemplate: boolean;
  warnings: Warning[];
}

export interface Warning {
  message: string;
  severity: "error" | "warning" | "info";
}

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
  iframes: DetectedIframe[];
  totalWarnings: number;
  sessionStorage: SessionStorageData | null;
  isQfdmoPage: boolean;
}
