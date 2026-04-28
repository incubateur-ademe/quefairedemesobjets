import { test, expect, Page, Frame, Locator, ElementHandle } from "@playwright/test"
import {
  navigateTo,
  TIMEOUT,
  searchCarteAndWaitForActeurs,
  clickFirstClickableActeurMarker,
  mockApiAdresse,
} from "./helpers"

// Helpers shared across iframe tracking tests
// These use Playwright's Frame API to evaluate JS directly inside the iframe,
// which works for both same-origin and cross-origin iframes (unlike contentWindow access).

async function getIframeFrame(page: Page): Promise<Frame> {
  // Wait until a child frame appears and has navigated to its URL
  await page.waitForFunction(() => window.frames.length > 0, {
    timeout: TIMEOUT.DEFAULT,
  })
  const frames = page.frames()
  const frame = frames.find((f) => f !== page.mainFrame())
  if (!frame) throw new Error("iframe frame not found")
  // Wait for the iframe page to finish loading before returning
  await frame.waitForLoadState("domcontentloaded", { timeout: TIMEOUT.LONG })
  return frame
}

async function waitForAnalyticsController(frame: Frame) {
  await frame.waitForFunction(
    () => {
      const w = window as any
      if (!w.stimulus) return false
      return !!w.stimulus.getControllerForElementAndIdentifier(
        document.body,
        "analytics",
      )
    },
    { timeout: TIMEOUT.LONG },
  )
}

async function installCaptureSpy(frame: Frame) {
  await frame.evaluate(() => {
    const w = window as any
    const ctrl = w.stimulus.getControllerForElementAndIdentifier(
      document.body,
      "analytics",
    )
    w.__capturedEvents = []
    const original = ctrl.capture.bind(ctrl)
    ctrl.capture = (event: string, props?: Record<string, unknown>) => {
      w.__capturedEvents.push({ event, props })
      original(event, props)
    }
  })
}

async function getCapturedEvents(frame: Frame): Promise<{ event: string }[]> {
  return frame.evaluate(() => {
    return (window as any).__capturedEvents as { event: string }[]
  })
}

async function waitForEvent(frame: Frame, eventName: string) {
  await frame.waitForFunction(
    (name) => {
      return (((window as any).__capturedEvents as { event: string }[]) ?? []).some(
        (e) => e.event === name,
      )
    },
    eventName,
    { timeout: TIMEOUT.DEFAULT },
  )
}

// Resolve the Frame object from an iframe Locator via its DOM handle.
// Using contentFrame() is redirect-safe: for iframes whose server redirects
// (e.g. /dechet -> /, /carte/<slug> -> /carte/<slug>/), URL-based matching
// on f.url() vs. the iframe src attribute would never match.
async function resolveIframeFrame(iframeEl: Locator): Promise<Frame> {
  let frame: Frame | null = null
  await expect
    .poll(
      async () => {
        const handle: ElementHandle | null = await iframeEl.elementHandle()
        frame = (await handle?.contentFrame()) ?? null
        return frame !== null && frame.url() !== "about:blank"
      },
      { timeout: TIMEOUT.LONG },
    )
    .toBe(true)
  return frame!
}

test.describe("📊 Analytics & Tracking", () => {
  test.describe("Tracking visibilité et interaction iframe (t_17)", () => {
    const TEST_PATH = "/lookbook/preview/tests/t_17_iframe_page_viewed/"

    test("iframe_page_viewed fires on scroll, interacted_with_iframe fires on hover, each only once", async ({
      page,
    }, testInfo) => {
      testInfo.setTimeout(90000)
      await navigateTo(page, TEST_PATH)

      const iframeEl = page.locator("iframe").first()
      await expect(iframeEl).toBeAttached({ timeout: TIMEOUT.DEFAULT })

      // Get the Frame object — works for both same-origin and cross-origin iframes
      const frame = await getIframeFrame(page)

      await waitForAnalyticsController(frame)
      await installCaptureSpy(frame)

      // No events yet — iframe is off-screen (2000px top padding)
      const eventsBefore = await getCapturedEvents(frame)
      expect(eventsBefore).toEqual([])

      // Scroll iframe into view on the parent page
      await iframeEl.scrollIntoViewIfNeeded()

      // iframe_page_viewed should fire via IntersectionObserver → postMessage
      await waitForEvent(frame, "iframe_page_viewed")
      const eventsAfterScroll = await getCapturedEvents(frame)
      expect(
        eventsAfterScroll.filter((e) => e.event === "iframe_page_viewed"),
      ).toHaveLength(1)

      // Hover inside the iframe body → interacted_with_iframe
      await frame.locator("main").first().hover()

      await waitForEvent(frame, "interacted_with_iframe")
      const eventsAfterHover = await getCapturedEvents(frame)
      expect(
        eventsAfterHover.filter((e) => e.event === "interacted_with_iframe"),
      ).toHaveLength(1)

      // Deduplication: scroll away, back, hover again — counts must stay at 1
      await page.evaluate(() => window.scrollTo(0, 0))
      await iframeEl.scrollIntoViewIfNeeded()
      await frame.locator("main").first().hover()
      await page.waitForTimeout(500)

      const finalEvents = await getCapturedEvents(frame)
      expect(finalEvents.filter((e) => e.event === "iframe_page_viewed")).toHaveLength(
        1,
      )
      expect(
        finalEvents.filter((e) => e.event === "interacted_with_iframe"),
      ).toHaveLength(1)
    })
  })

  test.describe("pageType et pageSlug dans les événements iframe (t_18)", () => {
    const TEST_PATH = "/lookbook/preview/tests/t_18_iframe_page_properties/"

    const iframeCases = [
      { testId: "iframe-carte", expectedPageType: "carte", expectedPageSlug: "" },
      {
        testId: "iframe-carte-sur-mesure",
        expectedPageType: "carte_sur_mesure",
        expectedPageSlug: null, // slug is dynamic, just check it's non-empty
      },
      {
        testId: "iframe-formulaire",
        expectedPageType: "formulaire",
        expectedPageSlug: "",
      },
      {
        testId: "iframe-assistant",
        expectedPageType: "quefaire",
        expectedPageSlug: "",
      },
    ]

    for (const { testId, expectedPageType, expectedPageSlug } of iframeCases) {
      test(`${testId} — iframe_page_viewed et interacted_with_iframe contiennent pageType="${expectedPageType}"`, async ({
        page,
      }, testInfo) => {
        testInfo.setTimeout(90000)
        await navigateTo(page, TEST_PATH)

        const iframeEl = page.locator(`[data-testid="${testId}"] iframe`).first()
        await expect(iframeEl).toBeAttached({ timeout: TIMEOUT.LONG })

        // Resolve Frame via DOM handle (redirect-safe; iframe src may differ from final URL)
        const resolvedFrame = await resolveIframeFrame(iframeEl)
        await resolvedFrame.waitForLoadState("domcontentloaded", {
          timeout: TIMEOUT.LONG,
        })
        await waitForAnalyticsController(resolvedFrame)
        await installCaptureSpy(resolvedFrame)

        // Scroll the iframe into view so the postMessage from the parent fires
        await iframeEl.scrollIntoViewIfNeeded()

        await waitForEvent(resolvedFrame, "iframe_page_viewed")
        const pageViewedEvents = await resolvedFrame.evaluate(() =>
          (
            (window as any).__capturedEvents as {
              event: string
              props?: Record<string, unknown>
            }[]
          ).filter((e) => e.event === "iframe_page_viewed"),
        )
        expect(pageViewedEvents).toHaveLength(1)
        expect(pageViewedEvents[0].props?.pageType).toBe(expectedPageType)
        if (expectedPageSlug !== null) {
          expect(pageViewedEvents[0].props?.pageSlug).toBe(expectedPageSlug)
        } else {
          // carte_sur_mesure: slug is dynamic, just verify it is a non-empty string
          expect(typeof pageViewedEvents[0].props?.pageSlug).toBe("string")
          expect(
            (pageViewedEvents[0].props?.pageSlug as string).length,
          ).toBeGreaterThan(0)
        }

        // Hover inside the iframe body to trigger interacted_with_iframe
        await resolvedFrame.locator("main").first().hover()
        await waitForEvent(resolvedFrame, "interacted_with_iframe")
        const interactedEvents = await resolvedFrame.evaluate(() =>
          (
            (window as any).__capturedEvents as {
              event: string
              props?: Record<string, unknown>
            }[]
          ).filter((e) => e.event === "interacted_with_iframe"),
        )
        expect(interactedEvents).toHaveLength(1)
        expect(interactedEvents[0].props?.pageType).toBe(expectedPageType)
        if (expectedPageSlug !== null) {
          expect(interactedEvents[0].props?.pageSlug).toBe(expectedPageSlug)
        } else {
          expect(typeof interactedEvents[0].props?.pageSlug).toBe("string")
          expect(
            (interactedEvents[0].props?.pageSlug as string).length,
          ).toBeGreaterThan(0)
        }
      })
    }
  })

  test.describe("UTM links dans les iframes (t_18)", () => {
    const TEST_PATH = "/lookbook/preview/tests/t_18_iframe_page_properties/"

    const iframeCases = [
      { testId: "iframe-carte", label: "carte" },
      { testId: "iframe-formulaire", label: "formulaire" },
      { testId: "iframe-assistant", label: "assistant" },
    ]

    for (const { testId, label } of iframeCases) {
      test(`${label} — les liens internes ont utm_source=qfdmod`, async ({
        page,
      }, testInfo) => {
        testInfo.setTimeout(90000)
        await navigateTo(page, TEST_PATH)

        const iframeEl = page.locator(`[data-testid="${testId}"] iframe`).first()
        await expect(iframeEl).toBeAttached({ timeout: TIMEOUT.LONG })

        const resolvedFrame = await resolveIframeFrame(iframeEl)
        await resolvedFrame.waitForLoadState("domcontentloaded", {
          timeout: TIMEOUT.LONG,
        })

        // Wait until at least one internal link exists in the iframe
        await expect(resolvedFrame.locator("a[href]").first()).toBeAttached({
          timeout: TIMEOUT.LONG,
        })

        // All same-origin links should carry utm_source=qfdmod
        const hrefs = await resolvedFrame.evaluate(() =>
          Array.from(document.querySelectorAll<HTMLAnchorElement>("a[href]"))
            .map((a) => a.href)
            .filter((href) => {
              try {
                return new URL(href).hostname === window.location.hostname
              } catch {
                return false
              }
            }),
        )

        expect(hrefs.length).toBeGreaterThan(0)
        for (const href of hrefs) {
          const url = new URL(href)
          expect(url.searchParams.get("utm_source")).toBe("qfdmod")
        }
      })
    }
  })

  test.describe("acteur_viewed event", () => {
    test("acteur_viewed fires with acteurUuid, acteurType and sources when opening acteur detail", async ({
      page,
    }) => {
      await mockApiAdresse(page)
      await navigateTo(page, "/carte")

      // Install capture spy on the page-level analytics controller
      await page.waitForFunction(
        () => {
          const w = window as any
          return !!w.stimulus?.getControllerForElementAndIdentifier(
            document.body,
            "analytics",
          )
        },
        { timeout: TIMEOUT.LONG },
      )
      await page.evaluate(() => {
        const w = window as any
        const ctrl = w.stimulus.getControllerForElementAndIdentifier(
          document.body,
          "analytics",
        )
        w.__capturedEvents = []
        const original = ctrl.capture.bind(ctrl)
        ctrl.capture = (event: string, props?: Record<string, unknown>) => {
          w.__capturedEvents.push({ event, props })
          original(event, props)
        }
      })

      await searchCarteAndWaitForActeurs(page, "Auray")
      await clickFirstClickableActeurMarker(page)

      // Wait for acteur_viewed to be captured
      await page.waitForFunction(
        () =>
          (((window as any).__capturedEvents as { event: string }[]) ?? []).some(
            (e) => e.event === "acteur_viewed",
          ),
        { timeout: TIMEOUT.DEFAULT },
      )

      const events = await page.evaluate(() =>
        (
          (window as any).__capturedEvents as {
            event: string
            props?: Record<string, unknown>
          }[]
        ).filter((e) => e.event === "acteur_viewed"),
      )

      expect(events).toHaveLength(1)
      expect(typeof events[0].props?.acteurUuid).toBe("string")
      expect((events[0].props?.acteurUuid as string).length).toBeGreaterThan(0)
      expect(typeof events[0].props?.acteurType).toBe("string")
      expect((events[0].props?.acteurType as string).length).toBeGreaterThan(0)
      expect(Array.isArray(events[0].props?.sources)).toBe(true)
      expect(typeof events[0].props?.searchAddress).toBe("string")
      expect((events[0].props?.searchAddress as string).length).toBeGreaterThan(0)
      expect(typeof events[0].props?.searchLatitude).toBe("string")
      expect(typeof events[0].props?.searchLongitude).toBe("string")
    })
  })

  test.describe("Tracking du referrer dans les iframes", () => {
    const scriptTypes = [
      { name: "carte", scriptType: "carte", iframeId: "carte", iframePath: "/carte" },
      {
        name: "assistant",
        scriptType: "assistant",
        iframeId: "assistant",
        iframePath: "/dechet",
      },
    ]

    for (const { name, scriptType, iframeId, iframePath } of scriptTypes) {
      test(`Le referrer parent avec query string est correctement passé à l'iframe pour ${name}`, async ({
        page,
      }) => {
        // Navigate to the test page with the script_type parameter and additional query params
        // The script_type selects which template to render via django-lookbook form
        const testQueryParams = "test_param=value&another=123"
        const fullUrl = `/lookbook/preview/tests/t_1_referrer?script_type=${scriptType}&${testQueryParams}`
        await navigateTo(page, fullUrl)

        // Get the parent window location for comparison (must include query params)
        const parentLocation = page.url()
        expect(parentLocation).toContain(testQueryParams)

        // Wait for the iframe to be created with the correct ID
        const iframeLocator = page.locator(`iframe#${iframeId}`)
        await expect(iframeLocator).toBeAttached({ timeout: TIMEOUT.DEFAULT })

        // Get the iframe src attribute and verify it contains the ref parameter
        const iframeSrc = await iframeLocator.getAttribute("src")
        expect(iframeSrc).not.toBeNull()
        expect(iframeSrc).toContain(iframePath)
        expect(iframeSrc).toContain("ref=")

        // Decode the ref parameter and verify it matches the parent URL
        const url = new URL(iframeSrc!, "http://localhost")
        const refParam = url.searchParams.get("ref")
        expect(refParam).not.toBeNull()

        // Decode base64 ref parameter
        const decodedRef = Buffer.from(refParam!, "base64").toString("utf-8")

        // Verify the decoded referrer contains the test query params
        expect(decodedRef).toContain(testQueryParams)
      })
    }
  })
})
