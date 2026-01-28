import { Controller } from "@hotwired/stimulus"
import { InteractionType as PosthogUIInteractionType } from "../../js/types"
import posthog, { PostHogConfig } from "posthog-js"
import { URL_PARAM_NAME_FOR_IFRAME_SCRIPT_MODE } from "../../js/helpers"

const IFRAME_REFERRER_SESSION_KEY = "qf_ifr"

type PersonProperties = {
  iframe: boolean
  iframeReferrer?: string
  iframeFromScript?: boolean
}

type UserConversionConfig = {
  homePageView: number
  produitPageView: number
  userInteractionWithMap: number
  userInteractionWithSolutionDetails: number
}

export default class extends Controller<HTMLElement> {
  /**
  A Posthog user has some custom values that we set
  - The user informations : email, username, admin (or not)
  - If the page loads in an iframe
  - The conversion score : if a user executes a specific set of actions, we consider
    it as converted. For example : see a Produit page, interact with the map, etc...
  */
  declare readonly initialActionValue
  declare readonly posthogDebugValue
  declare readonly posthogKeyValue
  declare readonly userAdminValue
  declare readonly userEmailValue
  declare readonly userUsernameValue
  declare userConversionScoreValue

  personProperties: PersonProperties = {
    iframe: false,
  }

  static values = {
    initialAction: String,
    posthogDebug: Boolean,
    posthogKey: String,
    userAdmin: Boolean,
    userConversionScore: Object,
    userEmail: String,
    userUsername: String,
  }

  intersectionObserverThreshold = 0.1

  posthogConfig: Partial<PostHogConfig> = {
    api_host: "https://eu.posthog.com",
    autocapture: false,
    capture_pageview: false,
    person_profiles: "always",
    persistence: "memory",
  }

  // The user conversion score is computed from several actions : page views,
  // clicks on specific UI areas, etc.
  //
  // Each action has it own score, for example a specific action
  // might score 2 points because of its importance.
  //
  // Each action is listed in the object below with the format :
  // { action name : points added when action is triggered }
  userConversionScoreConfig: UserConversionConfig = {
    homePageView: 0,
    produitPageView: 1,
    userInteractionWithMap: 1,
    userInteractionWithSolutionDetails: 1,
  }

  initialize(): void {
    posthog.init(this.posthogKeyValue, this.posthogConfig)
    this.#identifyAuthenticatedUser()
    this.#initialiseIframeRelatedPersonProperties()
    this.#syncSessionStorageWithLocalConversionScore()
    this.#setupIntersectionObserver()
    this.#computeConversionScoreFromSessionStorage()
    this.#setInitialActionValue()

    posthog.debug(!!this.posthogDebugValue)
  }

  userConversionScoreValueChanged(value) {
    this.#captureUserConversionScore()
    this.#syncSessionStorageWithLocalConversionScore()
  }

  // An initial action can be set in the template, as a Stimulus Value.
  // This value is read when initializing the controller, and set the default score.
  // For example, viewing the homepage or a Produit page scores 1 point.
  #setInitialActionValue() {
    if (
      this.initialActionValue &&
      !(this.initialActionValue in this.userConversionScoreConfig)
    ) {
      console.log(`${this.initialActionValue} is not a valid action value`)
      return
    }

    this.userConversionScoreValue = {
      ...this.userConversionScoreValue,
      [this.initialActionValue]:
        this.userConversionScoreConfig[this.initialActionValue],
    }
  }

  #syncSessionStorageWithLocalConversionScore() {
    for (const key of Object.keys(this.userConversionScoreConfig)) {
      if (key in this.userConversionScoreValue) {
        sessionStorage.setItem(key, this.userConversionScoreValue[key])
      }
    }
  }

  // This is used to discriminate authenticated users (LVAO Team)
  // from anonymous users.
  // In PostHog, authenticated users are excluded from insights.
  #identifyAuthenticatedUser() {
    if (this.userUsernameValue) {
      posthog.identify(this.userUsernameValue, {
        email: this.userEmailValue,
        admin: this.userAdminValue,
      })
    }
  }

  // The iframe URL parameter is not always set :
  // - After a navigation (click on a link)
  // - If the iframe integration does not use our script
  // In all these cases, we still want to determine
  // whether the user browse inside an iframe or not.
  #initialiseIframeRelatedPersonProperties() {
    const weAreInAnIframe = this.#areWeInAnIframe()
    this.personProperties.iframe = weAreInAnIframe

    const referrer = this.#fetchReferrer(weAreInAnIframe)
    if (referrer) {
      this.personProperties.iframeReferrer = referrer
    }

    const url = new URL(window.location.href)
    this.personProperties.iframeFromScript = url.searchParams.has(
      URL_PARAM_NAME_FOR_IFRAME_SCRIPT_MODE,
    )
  }

  #areWeInAnIframe(): boolean {
    let weAreInAnIframe = false

    try {
      if (window.self !== window.top) {
        weAreInAnIframe = true
      }
    } catch (e) {
      // Unable to access window.top
      // this might be due to cross-origin restrictions.
      // Assuming it's inside an iframe.
      weAreInAnIframe = true
    }

    return weAreInAnIframe
  }

  #fetchReferrer(weAreInAnIframe: boolean): string | undefined {
    let referrer

    // First, try to get the stored referrer from sessionStorage
    // This ensures we don't lose it on subsequent navigations
    const storedReferrer = sessionStorage.getItem(IFRAME_REFERRER_SESSION_KEY)
    if (storedReferrer) {
      referrer = storedReferrer
    }

    // Check if the referrer was passed via URL parameter from the iframe script
    // This is the most reliable method as it captures the full parent URL including query params
    const url = new URL(window.location.href)
    const encodedReferrer = url.searchParams.get("ref")
    if (encodedReferrer) {
      try {
        const decodedReferrer = atob(encodedReferrer)
        referrer = decodedReferrer
      } catch (e) {
        console.warn("Unable to decode referrer from URL parameter:", e)
      }
    }

    // For same-origin iframes, we can access the parent URL directly
    try {
      if (window.self !== window.top) {
        referrer = window.top?.location.href
      }
    } catch (e) {
      // Unable to access window.top due to cross-origin restrictions
    }

    // For cross-origin iframes, document.referrer contains the parent URL
    // But only on the first load - so we need to persist it
    if (document.referrer && !document.referrer.includes(document.location.origin)) {
      // Only set referrer if we don't already have one
      // This prevents overwriting the original referrer on subsequent navigations
      if (!referrer) {
        referrer = document.referrer
      }
    }

    // Persist the referrer in sessionStorage so it survives navigations
    // Only store if we have a referrer and are in an iframe
    if (weAreInAnIframe && referrer && !storedReferrer) {
      try {
        sessionStorage.setItem(IFRAME_REFERRER_SESSION_KEY, referrer)
      } catch (e) {
        // SessionStorage might not be available (privacy mode, etc.)
        console.warn("Unable to persist iframe referrer:", e)
      }
    }

    return referrer
  }

  #computeConversionScoreFromSessionStorage() {
    let conversionScore = {}
    for (const key of Object.keys(this.userConversionScoreConfig)) {
      if (sessionStorage.getItem(key)) {
        conversionScore[key] = parseInt(sessionStorage.getItem(key)!)
      }
    }

    this.userConversionScoreValue = {
      ...this.userConversionScoreValue,
      ...conversionScore,
    }
  }

  #updateDebugInspectorUI() {
    const posthogBannerConversionScore = document.querySelector(
      "#posthog-banner-conversion-score",
    )
    if (posthogBannerConversionScore) {
      posthogBannerConversionScore.textContent =
        this.userConversionScoreValue.toString()
    }
  }

  async #captureUserConversionScore() {
    posthog.capture("$set", {
      $set: {
        ...this.personProperties,
        conversionScore: this.#computeConversionScoreFromActions(),
        conversionActions: this.userConversionScoreValue,
      },
    })
    this.#updateDebugInspectorUI()
  }

  #computeConversionScoreFromActions() {
    let score = 0
    for (const value of Object.values(this.userConversionScoreValue)) {
      // TODO: type
      score += value as number
    }
    return score
  }

  #setupIntersectionObserver() {
    const observer = new IntersectionObserver(
      (entries, observer) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            posthog.capture("$pageview")
            // TODO: increase userConversionScore
            observer.unobserve(entry.target)
          }
        })
      },
      {
        root: null,
        threshold: this.intersectionObserverThreshold, // Trigger when at least 10% of the page is visible
      },
    )

    observer.observe(document.body)
  }

  #captureUIInteraction(
    userConversionKey: keyof UserConversionConfig,
    UIInteractionType: PosthogUIInteractionType,
  ) {
    const currentValue = this.userConversionScoreValue[userConversionKey] || 0
    this.userConversionScoreValue = {
      ...this.userConversionScoreValue,
      [userConversionKey]:
        currentValue + this.userConversionScoreConfig[userConversionKey],
    }
  }

  captureInteractionWithSolutionDetails() {
    this.#captureUIInteraction("userInteractionWithSolutionDetails", "solution_details")
  }

  captureInteractionWithMap() {
    this.#captureUIInteraction("userInteractionWithMap", "map")
  }
}
