import "@testing-library/jest-dom"

// Not implemented by jsdom
if (typeof URL.createObjectURL !== "function") {
  URL.createObjectURL = () => "blob:jest"
}

if (typeof Element !== "undefined") {
  Element.prototype.scrollIntoView = function scrollIntoView() {}
  Element.prototype.scrollTo = function scrollTo(
    this: Element,
    options?: ScrollToOptions | number,
  ) {
    if (typeof options === "object" && options.top !== undefined) {
      this.scrollTop = options.top
    }
  } as Element["scrollTo"]
}
