import { Controller } from "@hotwired/stimulus"
import { InteractionType as PosthogUIInteractionType, PosthogEventType } from "../../js/types"
import posthog, { PostHogConfig } from "posthog-js"
import { areWeInAnIframe } from "../../js/iframe"

type PersonProperties = {
  iframe: boolean
  iframeReferrer?: string
}

export default class extends Controller<HTMLElement> {
  /**
  A Posthog user has some custom values that we set
  - The user informations : email, username, admin (or not)
  - If the page loads in an iframe
  - The conversion score : if a user executes a specific set of actions, we consider
    it as converted. For example : see a Produit page, interact with the map, etc...
  */
  declare readonly actionValue
  declare readonly posthogDebugValue
  declare readonly posthogKeyValue
  declare readonly userAdminValue
  declare readonly userEmailValue
  declare readonly userUsernameValue
  declare userConversionScoreValue

  personProperties: PersonProperties = {
    iframe: false
  }

  static values = {
    action: String,
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
    person_profiles: 'always',
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
  userConversionScoreConfig = {
    homePageView: 1,
    produitPageView: 1,
    userInteractionWithMap: 1,
    userInteractionWithSolutionDetails: 1,
  }

  initialize(): void {
    posthog.init(this.posthogKeyValue, this.posthogConfig)
    this.#identifyAuthenticatedUser()
    this.#checkIfWeAreInAnIframe()
    this.#syncSessionStorageWithLocalConversionScore()
    this.#setupIntersectionObserverEvents()
    this.#setInitialActionValue()
    this.#computeConversionScoreFromSessionStorage()

    if (this.posthogDebugValue) {
      posthog.debug()
    }
  }

  userConversionScoreValueChanged(value, previousValue) {
    // TODO: compare values, use lodash ?
    // if (value !== previousValue) {
    this.#captureUserConversionScore()
    this.#syncSessionStorageWithLocalConversionScore()
    // }
  }


  // An initial action can be set in the template, as a Stimulus Value.
  // This value is read when initializing the controller, and set the default score.
  // For example, viewing the homepage or a Produit page scores 1 point.
  #setInitialActionValue() {
    if (this.actionValue && this.userConversionScoreConfig[this.actionValue]) {
      this.userConversionScoreValue[this.actionValue] = this.userConversionScoreConfig[this.actionValue]
    }
  }

  #syncSessionStorageWithLocalConversionScore() {
    for (const key of Object.keys(this.userConversionScoreConfig)) {
      sessionStorage.setItem(key, this.userConversionScoreConfig[this.actionValue])
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
  // - After a navigaation (click on a link)
  // - If the iframe integration does not use our script
  // In all these cases, we still want to determine
  // whether the user browse inside an iframe or not.
  #checkIfWeAreInAnIframe() {
    const [weAreInAnIframe, referrer] = areWeInAnIframe()
    this.personProperties.iframe = weAreInAnIframe
    this.personProperties.iframeReferrer = referrer
  }

  #computeConversionScoreFromSessionStorage() {
    let conversionScore = {}
    for (const key of Object.keys(this.userConversionScoreConfig)) {
      if (sessionStorage.getItem(key)) {
        conversionScore[key] = sessionStorage.getItem(key)
      }
    }

    this.userConversionScoreValue = conversionScore
  }

  #updateDebugInspectorUI() {
    const posthogBannerConversionScore = document.querySelector("#posthog-banner-conversion-score")
    if (posthogBannerConversionScore) {
      posthogBannerConversionScore.textContent = this.userConversionScoreValue.toString()
    }
  }

  async #captureUserConversionScore() {
    posthog.capture("$set", {
      $set: {
        ...this.personProperties,
        conversionScore: this.userConversionScoreValue,
      },
    })
    this.#updateDebugInspectorUI()
  }

  #setupIntersectionObserverEvents() {
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
        threshold: this.intersectionObserverThreshold,  // Trigger when at least 10% of the page is visible
      },
    )

    observer.observe(document.body)
  }

  // TODO: type
  captureUIInteraction(UIInteractionType: PosthogUIInteractionType) {
    const key = "userInteractionWithMap"
    this.userConversionScoreValue = {
      ...this.userConversionScoreValue,
      [key]: this.userConversionScoreValue[key] + this.userConversionScoreConfig[key],
    }
  }

  captureInteractionWithSolutionDetails() {
    this.captureUIInteraction("userInteractionWithMap")
  }

  captureInteractionWithMap() {
    this.captureUIInteraction("userInteractionWithSolutionDetails")
  }
}
