import posthog from "posthog-js"

if (process.env.NODE_ENV !== "development") {
    posthog.init("phc_SGbYOrenShCMKJOQYyl62se9ZqCHntjTlzgKNhrKnzm", {
        api_host: "https://eu.posthog.com",
    })
}

export default posthog
