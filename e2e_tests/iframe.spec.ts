
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
    "http://localhost:8000?iframe=1&direction=jai&first_dir=jai&action_list=reparer%7Cechanger%7Cmettreenlocation%7Crevendre"
  );
  expect(frameborder).toBe("0");
  expect(scrolling).toBe("no");
  expect(allowfullscreen).toBe("true");
  expect(style).toContain("width: 100%;");
  expect(style).toContain("height: 720px;");
  expect(style).toContain("max-width: 800px;");
  expect(title).toBe("Longue vie aux objets");
}

test("iframe is loaded with correct parameters", async ({ page }) => {
  await page.goto("http://localhost:8000/test_iframe", { waitUntil: "networkidle" });

  const titlePage = await page.title();
  expect(titlePage).toBe("IFrame test : QFDMO");

  const iframeElement = await page.$("iframe");
  await expectIframeAttributes(iframeElement);
});

test("form is visible in the iframe", async ({ page }) => {
  await page.goto("http://localhost:8000/test_iframe", { waitUntil: "networkidle" });

  const iframeElement = await page.$("iframe");
  const iframe = await iframeElement?.contentFrame();
  const form = await iframe?.$("#search_form");
  expect(form).not.toBeNull();

  const formHeight = await iframe?.$eval("[data-testid='form-content']", el => el.offsetHeight);
  expect(formHeight).toBeGreaterThan(600);
});

test("iframe with 0px parent height displays correctly", async ({ page }) => {
  await page.goto("http://localhost:8000/test_iframe?carte=1", { waitUntil: "networkidle" });
  await expect(page).toHaveScreenshot("iframe.png");

  await page.goto("http://localhost:8000/test_iframe?no-height=1&carte=1", { waitUntil: "networkidle" });
  await page.evaluate(() => {
    document.querySelector("[data-testid=iframe-no-height-wrapper]")?.setAttribute("style", "");
  });
  await page.waitForTimeout(1000);
  await expect(page).toHaveScreenshot("iframe.png");
});
