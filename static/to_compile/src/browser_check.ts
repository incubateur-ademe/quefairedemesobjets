import * as Bowser from "bowser"

function isBrowserSupported(): boolean {
    const browser = Bowser.getParser(window.navigator.userAgent)
    const isValidBrowser = browser.satisfies({
        // declare browsers and versions you want to support
        // 2017
        chrome: ">60",
        // 2017
        firefox: ">55",
        // 2017
        safari: ">10",
        // 2019
        opera: ">50",
        edge: ">15",
        ie: "none",
    })

    return isValidBrowser
}

document.addEventListener("DOMContentLoaded", function () {
    if (!isBrowserSupported()) {
        document
            .getElementById("obsolete_browser_message")
            .classList.remove("qfdmo-hidden")
    }
})
