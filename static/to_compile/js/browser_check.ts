import * as Bowser from "bowser"

function isBrowserSupported(): boolean {
    const browser = Bowser.getParser(window.navigator.userAgent)
    let isValidBrowser = browser.satisfies({
        // declare browsers and versions you want to support
        chrome: ">=88",
        firefox: ">=79",
        safari: ">=14",
        opera: ">=74",
        edge: ">=88",
        ie: "none",
    })
    if (isValidBrowser === undefined) {
        isValidBrowser = true
    }

    return isValidBrowser
}

document.addEventListener("DOMContentLoaded", function () {
    if (!isBrowserSupported()) {
        document
            ?.getElementById("obsolete_browser_message")
            ?.classList.remove("qf-hidden")
    }
})
