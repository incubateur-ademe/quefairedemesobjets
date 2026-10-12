import "@testing-library/jest-dom"

// Not implemented by jsdom
if (typeof URL.createObjectURL !== "function") {
  URL.createObjectURL = () => "blob:jest"
}

if (typeof Element !== "undefined") {
  Element.prototype.scrollIntoView = function scrollIntoView() {}
}
