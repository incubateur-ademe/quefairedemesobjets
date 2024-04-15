import * as Bowser from "bowser"

function isBrowserSupported(): boolean {
    const browser = Bowser.getParser(window.navigator.userAgent)
    const isValidBrowser = browser.satisfies({
        // declare browsers and versions you want to support
        chrome: ">85",
        firefox: ">79",
        safari: ">=14",
        opera: ">70",
        edge: ">84",
        ie: "none",
    })

    return isValidBrowser !== false
}

document.addEventListener("DOMContentLoaded", function () {
    if (!isBrowserSupported()) {
        document
            .getElementById("obsolete_browser_message")
            .classList.remove("qfdmo-hidden")
    }
})
