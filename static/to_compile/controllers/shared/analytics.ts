import { Controller } from "@hotwired/stimulus"
import { InteractionType as PosthogUIInteractionType, PosthogEventType } from "../../js/types"
import posthog, { PostHogConfig } from "posthog-js"
import { areWeInAnIframe } from "../../js/iframe"

type PersonProperties = {
  iframe: boolean
  iframeReferrer?: string
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
    iframe: false
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
  userConversionScoreConfig: UserConversionConfig = {
    homePageView: 0,
    produitPageView: 1,
    userInteractionWithMap: 1,
    userInteractionWithSolutionDetails: 1,
  }

  initialize(): void {
    posthog.init(this.posthogKeyValue, this.posthogConfig)
    this.#identifyAuthenticatedUser()
    this.#checkIfWeAreInAnIframe()
    this.#syncSessionStorageWithLocalConversionScore()
    this.#setupIntersectionObserver()
    this.#computeConversionScoreFromSessionStorage()
    this.#setInitialActionValue()

    if (this.posthogDebugValue) {
      posthog.debug()
    }
  }

  userConversionScoreValueChanged(value) {
    this.#captureUserConversionScore()
    this.#syncSessionStorageWithLocalConversionScore()
  }


  // An initial action can be set in the template, as a Stimulus Value.
  // This value is read when initializing the controller, and set the default score.
  // For example, viewing the homepage or a Produit page scores 1 point.
  #setInitialActionValue() {
    if (this.initialActionValue && !(this.initialActionValue in this.userConversionScoreConfig)) {
      console.log(`${this.initialActionValue} is not a valid action value`)
      return
    }

    this.userConversionScoreValue = {
      ...this.userConversionScoreValue,
      [this.initialActionValue]: this.userConversionScoreConfig[this.initialActionValue]
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
  #checkIfWeAreInAnIframe() {
    const [weAreInAnIframe, referrer] = areWeInAnIframe()
    this.personProperties.iframe = weAreInAnIframe
    this.personProperties.iframeReferrer = referrer
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
      ...conversionScore
    }
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
        threshold: this.intersectionObserverThreshold,  // Trigger when at least 10% of the page is visible
      },
    )

    observer.observe(document.body)
  }

  #captureUIInteraction(userConversionKey: keyof UserConversionConfig, UIInteractionType: PosthogUIInteractionType) {
    const currentValue = this.userConversionScoreValue[userConversionKey] || 0
    this.userConversionScoreValue = {
      ...this.userConversionScoreValue,
      [userConversionKey]: currentValue + this.userConversionScoreConfig[userConversionKey],
    }
  }

  captureInteractionWithSolutionDetails() {
    this.#captureUIInteraction("userInteractionWithSolutionDetails", "solution_details")
  }

  captureInteractionWithMap() {
    this.#captureUIInteraction("userInteractionWithMap", "map")
  }
}
