function postHeightSize(): void {
    const target: Window | undefined = parent.postMessage ? parent : undefined

    if (target && document.body.scrollHeight) {
        target.postMessage(document.body.scrollHeight, "*")
    }
}

window.addEventListener("load", function (): void {
    postHeightSize()
})
