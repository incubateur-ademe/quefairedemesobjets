import "@testing-library/jest-dom"

// Not implemented by jsdom
if (typeof Element !== "undefined") {
  Element.prototype.scrollIntoView = function scrollIntoView() {}
}
