import { getIframeAttributesAndExtra } from "../entrypoints/iframe_functions";

describe("getIframeAttributesAndExtra function tests", () => {
  let scriptTag: HTMLScriptElement;

  // Helper function to set dataset attributes
  const setScriptDataset = (attributes: { [key: string]: string }) => {
    Object.entries(attributes).forEach(([key, value]) => {
      scriptTag.dataset[key] = value;
    });
  };

  // Reusable function for asserting iframe attributes
  const assertIframeAttributes = (iframeAttributes: any, expectedSrc: string) => {
    expect(iframeAttributes.src).toBe(expectedSrc);
    expect(iframeAttributes).toStrictEqual({
      allow: "geolocation; clipboard-write",
      allowFullscreen: true,
      frameBorder: "0",
      id: "lvao_iframe",
      scrolling: "no",
      src: expectedSrc,
      style: "overflow: hidden; max-width: 100%; width: 100%; height: 700px;",
      title: "Longue vie aux objets",
    });
  };

  beforeEach(() => {
    scriptTag = document.createElement("script");
    scriptTag.src = "https://example.com/script.js";
  });

  test.each([
    {
      description: "with bounding box",
      dataset: {
        address_placeholder: "toto,tata",
        bounding_box:
          '{"southWest": {"lat": 48.916, "lng": 2.298202514648438}, "northEast": {"lat": 48.98742568330284, "lng": 2.483596801757813}}',
        direction: "jai",
      },
      initialParams: ["carte", "1"],
      expectedSrc:
        "https://example.com?carte=1&address_placeholder=toto%2Ctata&bounding_box=%7B%22southWest%22%3A%7B%22lat%22%3A48.916%2C%22lng%22%3A2.298202514648438%7D%2C%22northEast%22%3A%7B%22lat%22%3A48.98742568330284%2C%22lng%22%3A2.483596801757813%7D%7D&direction=jai",
    },
    {
      description: "with a single EPCI code",
      dataset: {
        action_list: "acheter|revendre|preter|emprunter|louer|mettreenlocation|donner|echanger|reparer",
        epci_codes: "200073146",
        limit: "71",
      },
      initialParams: ["carte", "1"],
      expectedSrc:
        "https://example.com?carte=1&action_list=acheter%7Crevendre%7Cpreter%7Cemprunter%7Clouer%7Cmettreenlocation%7Cdonner%7Cechanger%7Creparer&epci_codes=200073146&limit=71",
    },
    {
      description: "with multiple EPCI codes",
      dataset: {
        action_list: "acheter|revendre|preter|emprunter|louer|mettreenlocation|donner|echanger|reparer",
        epci_codes: "200073146,200040442,245804497",
        limit: "71",
      },
      initialParams: ["carte", "1"],
      expectedSrc:
        "https://example.com?carte=1&action_list=acheter%7Crevendre%7Cpreter%7Cemprunter%7Clouer%7Cmettreenlocation%7Cdonner%7Cechanger%7Creparer&epci_codes=200073146&epci_codes=200040442&epci_codes=245804497&limit=71",
    },
  ])(
    "should generate correct iframe attributes $description",
    ({ dataset, initialParams, expectedSrc }) => {
      // These are tests...any seems acceptable but we might want to type this at some point.
      setScriptDataset(dataset as any);

      const [iframeAttributes, iframeExtraAttributes] = getIframeAttributesAndExtra(
        initialParams as [string, string],
        scriptTag
      );

      assertIframeAttributes(iframeAttributes, expectedSrc);
      expect(iframeExtraAttributes).toBeDefined();
    }
  );
});
