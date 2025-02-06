
import { expect, test } from "@playwright/test"

// Helper function to check iframe attributes
async function expectIframeAttributes(iframeElement) {
  const attributes = await Promise.all([
    iframeElement?.getAttribute("allow"),
    iframeElement?.getAttribute("src"),
    iframeElement?.getAttribute("frameborder"),
    iframeElement?.getAttribute("scrolling"),
    iframeElement?.getAttribute("allowfullscreen"),
    iframeElement?.getAttribute("style"),
    iframeElement?.getAttribute("title")
  ]);

  const [
    allow, src, frameborder, scrolling, allowfullscreen, style, title
  ] = attributes;

  expect(allow).toBe("geolocation; clipboard-write");
  expect(src).toBe(
    "http://localhost:8000/formulaire?direction=jai&first_dir=jai&action_list=reparer%7Cechanger%7Cmettreenlocation%7Crevendre"
  );
  expect(frameborder).toBe("0");
  expect(scrolling).toBe("no");
  expect(allowfullscreen).toBe("true");
  expect(style).toContain("width: 100%;");
  expect(style).toContain("height: 720px;");
  expect(style).toContain("max-width: 800px;");
  expect(title).toBe("Longue vie aux objets");
}

test("Desktop | iframe formulaire is loaded with correct parameters", async ({ page }) => {
  await page.goto("http://localhost:8000/test_iframe", { waitUntil: "networkidle" });

  const titlePage = await page.title();
  expect(titlePage).toBe("IFrame test : QFDMO");

  const iframeElement = await page.$("iframe");
  await expectIframeAttributes(iframeElement);
});

test("Desktop | legacy iframe urls still work", async ({ page }) => {
  await page.goto("http://localhost:8000/?iframe=1&direction=jai&first_dir=jai&action_list=reparer%7Cechanger%7Cmettreenlocation%7Crevendre&BYPASS_ASSISTANT",
    { waitUntil: "networkidle" }
  )
  await expect(page).toHaveURL("http://localhost:8000/formulaire?direction=jai&first_dir=jai&action_list=reparer%7Cechanger%7Cmettreenlocation%7Crevendre")

  await page.goto("http://localhost:8000/?carte=1&action_list=reparer%7Cdonner%7Cechanger%7Cpreter%7Cemprunter%7Clouer%7Cmettreenlocation%7Cacheter%7Crevendre&epci_codes=200055887&limit=50&BYPASS_ASSISTANT"
    , { waitUntil: "networkidle" }
  )
  await expect(page).toHaveURL("http://localhost:8000/carte?action_list=reparer%7Cdonner%7Cechanger%7Cpreter%7Cemprunter%7Clouer%7Cmettreenlocation%7Cacheter%7Crevendre&epci_codes=200055887&limit=50")
});

test("Desktop | form is visible in the iframe", async ({ page }) => {
  await page.goto("http://localhost:8000/test_iframe", { waitUntil: "networkidle" });

  const iframeElement = await page.$("iframe");
  const iframe = await iframeElement?.contentFrame();
  const form = await iframe?.$("#search_form");
  expect(form).not.toBeNull();

  const formHeight = await iframe?.$eval("[data-testid='form-content']", el => el.offsetHeight);
  expect(formHeight).toBeGreaterThan(600);
});

test("Desktop | iframe with 0px parent height displays correctly", async ({ page }) => {
  await page.goto("http://localhost:8000/test_iframe?carte=1", { waitUntil: "networkidle" });
  await expect(page).toHaveScreenshot("iframe.png");

  await page.goto("http://localhost:8000/test_iframe?no-height=1&carte=1", { waitUntil: "networkidle" });
  await page.evaluate(() => {
    document.querySelector("[data-testid=iframe-no-height-wrapper]")?.setAttribute("style", "");
  });
  await page.waitForTimeout(1000);
  await expect(page).toHaveScreenshot("iframe.png");
});

test("Desktop | iframe cannot read the referrer when referrerPolicy is set to no-referrer", async ({ page }) => {
  await page.goto("http://localhost:8000/test_iframe?carte=1&noreferrer", { waitUntil: "networkidle" });

  // Get the content frame of the iframe
  const iframeElement = await page.$("iframe[referrerpolicy='no-referrer']");
  const iframe = await iframeElement?.contentFrame();
  expect(iframe).toBeTruthy();

  // Evaluate the referrer inside the iframe
  const referrer = await iframe?.evaluate(() => document.referrer);

  // Assert that the referrer is set and not undefined
  expect(referrer).toBe('');
});

test("iframe can read the referrer when referrerPolicy is not set", async ({ page }) => {
  await page.goto("http://localhost:8000/test_iframe?carte=1", { waitUntil: "networkidle" });

  // Get the content frame of the iframe
  const iframeElement = await page.$("iframe[data-testid='assistant']");
  const iframe = await iframeElement?.contentFrame();
  expect(iframe).not.toBeNull();

  // Evaluate the referrer inside the iframe
  const referrer = await iframe.evaluate(() => document.referrer);

  // Assert that the referrer is set and not undefined
  expect(referrer).toBe('http://localhost:8000/test_iframe?carte=1');
});

// Need to be run locally with nginx running
// test("Desktop | iframe mode is kept during navigation", async ({ browser, page }) => {
//   await page.goto("http://localhost:8001/dechet/chaussures?iframe", { waitUntil: "networkidle" });
//   page.getByTestId("header-logo-link").click()
//   await expect(page).toHaveURL("http://localhost:8001/dechet/")
//   expect(await page.$("body > footer")).toBeFalsy()
//   await page.close()

//   const newPage = await browser.newPage()
//   await newPage.goto("http://localhost:8001/dechet/chaussures", { waitUntil: "networkidle" });
//   expect(browser.contexts)
//   expect(await newPage.$("body > footer")).toBeTruthy()
//   await newPage.close()

//   const yetAnotherPage = await browser.newPage()
//   await yetAnotherPage.goto("http://localhost:8001/dechet/chaussures?iframe", { waitUntil: "networkidle" });
//   await yetAnotherPage.goto("http://localhost:8001/dechet/", { waitUntil: "networkidle" });
//   await yetAnotherPage.goto("http://localhost:8001/dechet/chaussures", { waitUntil: "networkidle" });
//   expect(await yetAnotherPage.$("body > footer")).not.toBeTruthy()
// });
