import { generateBackLink } from "../embed/helpers"
import { getIframeAttributesAndExtra } from "../js/iframe_functions"

describe("generateBackLink", () => {
  let iframeMock: HTMLIFrameElement

  beforeEach(() => {
    iframeMock = document.createElement("iframe")
    document.body.appendChild(iframeMock)
  })

  afterEach(() => {
    document.body.removeChild(iframeMock)
    jest.restoreAllMocks()
  })

  it("should log an error and not proceed when origin is undefined or empty", async () => {
    console.error = jest.fn() // Mock console.error to track errors

    // Test for undefined origin
    await generateBackLink(iframeMock, "carte", undefined)
    expect(console.error).toHaveBeenCalledWith("Origin is not defined or is empty")

    // Test for empty string origin
    await generateBackLink(iframeMock, "carte", "")
    expect(console.error).toHaveBeenCalledWith("Origin is not defined or is empty")

    // Test for null origin
    await generateBackLink(iframeMock, "carte", null)
    expect(console.error).toHaveBeenCalledWith("Origin is not defined or is empty")
  })
})

describe("getIframeAttributesAndExtra function tests", () => {
  let scriptTag: HTMLScriptElement

  // Helper function to set dataset attributes
  const setScriptDataset = (attributes: Record<string, string | undefined>) => {
    Object.entries(attributes).forEach(([key, value]) => {
      if (value !== undefined) {
        scriptTag.dataset[key] = value
      }
    })
  }

  // Reusable function for asserting iframe attributes
  const assertIframeAttributes = (iframeAttributes: any, expectedSrc: string) => {
    expect(iframeAttributes.src).toBe(expectedSrc)
    expect(iframeAttributes).toStrictEqual({
      allow: "geolocation; clipboard-write",
      allowFullscreen: true,
      frameBorder: "0",
      id: "lvao_iframe",
      scrolling: "no",
      src: expectedSrc,
      style: "overflow: hidden; max-width: 100%; width: 100%; height: 700px;",
      title: "Que faire de mes objets et déchets",
    })
  }

  beforeEach(() => {
    scriptTag = document.createElement("script")
    scriptTag.src = `${process.env.BASE_URL}/script.js`
  })

  test.each([
    {
      description: "with bounding box",
      dataset: {
        address_placeholder: "toto,tata",
        bounding_box:
          '{"southWest": {"lat": 48.916, "lng": 2.298202514648438}, "northEast": {"lat": 48.98742568330284, "lng": 2.483596801757813}}',
        direction: "jai",
      },
      route: "carte",
      options: { height: "700px" },
      expectedSrc: `${process.env.BASE_URL}/carte?ref=aHR0cDovL2xvY2FsaG9zdC8%3D&address_placeholder=toto%2Ctata&bounding_box=%7B%22southWest%22%3A%7B%22lat%22%3A48.916%2C%22lng%22%3A2.298202514648438%7D%2C%22northEast%22%3A%7B%22lat%22%3A48.98742568330284%2C%22lng%22%3A2.483596801757813%7D%7D&direction=jai`,
    },
    {
      description: "with a single EPCI code",
      dataset: {
        action_list:
          "acheter|revendre|preter|emprunter|louer|mettreenlocation|donner|echanger|reparer",
        epci_codes: "200073146",
        limit: "71",
      },
      route: "carte",
      options: { height: "700px" },
      expectedSrc: `${process.env.BASE_URL}/carte?ref=aHR0cDovL2xvY2FsaG9zdC8%3D&action_list=acheter%7Crevendre%7Cpreter%7Cemprunter%7Clouer%7Cmettreenlocation%7Cdonner%7Cechanger%7Creparer&epci_codes=200073146&limit=71`,
    },
    {
      description: "with multiple EPCI codes",
      dataset: {
        action_list:
          "acheter|revendre|preter|emprunter|louer|mettreenlocation|donner|echanger|reparer",
        epci_codes: "200073146,200040442,245804497",
        limit: "71",
      },
      route: "carte",
      options: { height: "700px" },
      expectedSrc: `${process.env.BASE_URL}/carte?ref=aHR0cDovL2xvY2FsaG9zdC8%3D&action_list=acheter%7Crevendre%7Cpreter%7Cemprunter%7Clouer%7Cmettreenlocation%7Cdonner%7Cechanger%7Creparer&epci_codes=200073146&epci_codes=200040442&epci_codes=245804497&limit=71`,
    },
  ])(
    "should generate correct iframe attributes $description",
    ({
      dataset,
      route,
      options,
      expectedSrc,
    }: {
      dataset: Record<string, string | undefined>
      route: string
      options: Record<string, unknown>
      expectedSrc: string
    }) => {
      // These are tests...any seems acceptable but we might want to type this at some point.
      setScriptDataset(dataset)

      const [iframeAttributes, iframeExtraAttributes] = getIframeAttributesAndExtra(
        scriptTag,
        route,
        options as any,
      )

      assertIframeAttributes(iframeAttributes, expectedSrc)
      expect(iframeExtraAttributes).toBeDefined()
    },
  )

  test("should use default height (100vh) for assistant iframe", () => {
    setScriptDataset({ objet: "test-objet" })

    const [iframeAttributes] = getIframeAttributesAndExtra(scriptTag, "dechet", {
      useAutoHeight: true,
      addScriptModeParam: true,
    })

    expect(iframeAttributes.style).toBe(
      "overflow: hidden; max-width: 100%; width: 100%; height: 100vh;",
    )
    expect(iframeAttributes.src).toBe(
      `${process.env.BASE_URL}/dechet/test-objet?s=1&ref=aHR0cDovL2xvY2FsaG9zdC8%3D`,
    )
  })

  test("should use default height (100vh) for formulaire iframe", () => {
    const [iframeAttributes] = getIframeAttributesAndExtra(scriptTag, "formulaire", {
      maxWidth: "800px",
    })

    expect(iframeAttributes.style).toBe(
      "overflow: hidden; max-width: 800px; width: 100%; height: 100vh;",
    )
    expect(iframeAttributes.src).toBe(
      `${process.env.BASE_URL}/formulaire?ref=aHR0cDovL2xvY2FsaG9zdC8%3D`,
    )
  })

  test("should use default height (100vh) for infotri iframe", () => {
    setScriptDataset({ categorie: "tous", consigne: "1" })

    const [iframeAttributes] = getIframeAttributesAndExtra(scriptTag, "infotri", {
      useAutoHeight: true,
    })

    expect(iframeAttributes.style).toBe(
      "overflow: hidden; max-width: 100%; width: 100%; height: 100vh;",
    )
    expect(iframeAttributes.src).toBe(
      `${process.env.BASE_URL}/infotri?ref=aHR0cDovL2xvY2FsaG9zdC8%3D&categorie=tous&consigne=1`,
    )
  })
})
