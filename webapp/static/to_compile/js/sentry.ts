import * as Sentry from "@sentry/browser"

export function initSentry(dsn: string, environment: string) {
  if (!dsn) return
  Sentry.init({
    dsn,
    environment,
    tracesSampleRate: 0.01,
    integrations: [Sentry.browserTracingIntegration()],
  })
}
