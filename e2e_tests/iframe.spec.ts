
import { expect } from "@playwright/test"
import { test } from "./config"

test("Desktop | iframe formulaire is loaded with correct parameters", async ({ page, carteUrl }) => {
  await page.goto(`${carteUrl}/test_iframe`, { waitUntil: "networkidle" });

  const titlePage = await page.title();
  expect(titlePage).toBe("IFrame test : QFDMO");

  const iframeElement = await page.$("iframe");
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
    `${carteUrl}/formulaire?direction=jai&first_dir=jai&action_list=reparer%7Cechanger%7Cmettreenlocation%7Crevendre`
  );
  expect(frameborder).toBe("0");
  expect(scrolling).toBe("no");
  expect(allowfullscreen).toBe("true");
  expect(style).toContain("width: 100%;");
  expect(style).toContain("height: 720px;");
  expect(style).toContain("max-width: 800px;");
  expect(title).toBe("Longue vie aux objets");
});

test("Desktop | legacy iframe urls still work", async ({ page, carteUrl }) => {
  await page.goto(`${carteUrl}/?iframe=1&direction=jai&first_dir=jai&action_list=reparer%7Cechanger%7Cmettreenlocation%7Crevendre&BYPASS_ASSISTANT`,
    { waitUntil: "networkidle" }
  )
  await expect(page).toHaveURL(`${carteUrl}/formulaire?direction=jai&first_dir=jai&action_list=reparer%7Cechanger%7Cmettreenlocation%7Crevendre`)
  await page.goto(`${carteUrl}/?carte=1&action_list=reparer%7Cdonner%7Cechanger%7Cpreter%7Cemprunter%7Clouer%7Cmettreenlocation%7Cacheter%7Crevendre&epci_codes=200055887&limit=50&BYPASS_ASSISTANT`, { waitUntil: "networkidle" })
  await expect(page).toHaveURL(`${carteUrl}/carte?action_list=reparer%7Cdonner%7Cechanger%7Cpreter%7Cemprunter%7Clouer%7Cmettreenlocation%7Cacheter%7Crevendre&epci_codes=200055887&limit=50`)
});

test("Desktop | form is visible in the iframe", async ({ page, carteUrl }) => {
  await page.goto(`${carteUrl}/test_iframe`, { waitUntil: "networkidle" });

  const iframeElement = await page.$("iframe");
  const iframe = await iframeElement?.contentFrame();
  const form = await iframe?.$("#search_form");
  expect(form).not.toBeNull();

  const formHeight = await iframe?.$eval("[data-testid='form-content']", el => el.offsetHeight);
  expect(formHeight).toBeGreaterThan(600);
});

test("Desktop | iframe with 0px parent height displays correctly", async ({ page, carteUrl }) => {
  await page.goto(`${carteUrl}/test_iframe?carte=1`, { waitUntil: "networkidle" });
  await expect(page).toHaveScreenshot("iframe.png");

  await page.goto(`${carteUrl}/test_iframe?noheight=1&carte=1`, { waitUntil: "networkidle" });
  await page.evaluate(() => {
    document.querySelector("[data-testid=iframe-no-height-wrapper]")?.setAttribute("style", "");
  });
  await page.waitForTimeout(1000);
  await expect(page).toHaveScreenshot("iframe.png");
});

test("Desktop | iframe cannot read the referrer when referrerPolicy is set to no-referrer", async ({ page, carteUrl }) => {
  await page.goto(`${carteUrl}/test_iframe?carte=1&noreferrer`, { waitUntil: "networkidle" });

  // Get the content frame of the iframe
  const iframeElement = await page.$("iframe[referrerpolicy='no-referrer']");
  const iframe = await iframeElement?.contentFrame();
  expect(iframe).toBeTruthy();

  // Evaluate the referrer inside the iframe
  const referrer = await iframe?.evaluate(() => document.referrer);

  // Assert that the referrer is set and not undefined
  expect(referrer).toBe('');
});

test("iframe can read the referrer when referrerPolicy is not set", async ({ page, carteUrl }) => {
  await page.goto(`${carteUrl}/test_iframe?carte=1`, { waitUntil: "networkidle" });

  // Get the content frame of the iframe
  const iframeElement = await page.$("iframe[data-testid='assistant']");
  const iframe = await iframeElement?.contentFrame();
  expect(iframe).not.toBeNull();

  // Evaluate the referrer inside the iframe
  const referrer = await iframe.evaluate(() => document.referrer);

  // Assert that the referrer is set and not undefined
  expect(referrer).toBe(`${carteUrl}/test_iframe?carte=1`);
});

// Need to be run locally with nginx running
test("Desktop | iframe mode is kept during navigation", async ({ browser, page, carteUrl, assistantUrl }) => {
  await page.goto(`${assistantUrl}/dechet/chaussures?iframe`, { waitUntil: "networkidle" });
  page.getByTestId("header-logo-link").click()
  await expect(page).toHaveURL(`${assistantUrl}`)
  expect(await page.$("body > footer")).toBeFalsy()
  await page.close()

  const newPage = await browser.newPage()
  await newPage.goto(`${assistantUrl}/dechet/chaussures`, { waitUntil: "networkidle" });
  expect(browser.contexts)
  expect(await newPage.$("body > footer")).toBeTruthy()
  await newPage.close()
  const yetAnotherPage = await browser.newPage()
  await yetAnotherPage.goto(`${assistantUrl}/dechet/chaussures?iframe`, { waitUntil: "networkidle" });
  await yetAnotherPage.goto(`${assistantUrl}`, { waitUntil: "networkidle" });
  await yetAnotherPage.goto(`${assistantUrl}/dechet/chaussures`, { waitUntil: "networkidle" });
  expect(await yetAnotherPage.$("body > footer")).not.toBeTruthy()
});
