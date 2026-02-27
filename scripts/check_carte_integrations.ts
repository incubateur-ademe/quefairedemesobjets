#!/usr/bin/env npx tsx
/**
 * Batch check script to detect QFDMO iframe/script integrations on a list of URLs.
 * Reuses the same detection logic as the Chrome extension.
 *
 * Usage:
 *   NODE_PATH=webapp/node_modules npx tsx scripts/check_carte_integrations.ts <input> <output.csv>
 *
 * Input formats:
 *   - Text file: one URL per line
 *   - CSV file: reads URLs from column "Lien carte ou données"
 *
 * Dependencies (from webapp/node_modules):
 *   - @playwright/test (Playwright browser automation)
 *   - tsx (TypeScript execution)
 *
 * Note: NODE_PATH is required because the script lives in scripts/ but
 * dependencies are installed in webapp/node_modules.
 */

import { chromium } from "@playwright/test";
import * as fs from "fs";
import * as path from "path";
import {
  type DetectionConfig,
  type DetectedIframe,
  type DetectedScript,
  detectIframeIntegrations,
  detectScriptIntegrations,
  buildDetectionConfig,
} from "../webapp/static/to_compile/js/shared_detection";
import {
  KNOWN_DOMAINS,
  MAIN_DOMAIN,
  CARTE_ROUTE,
  FORMULAIRE_ROUTE,
  DECHET_ROUTE,
  CARTE_SCRIPT_FILENAME,
  FORMULAIRE_SCRIPT_FILENAME,
} from "../webapp/static/to_compile/js/shared_constants";

// -- Config --

const USER_AGENT =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
  "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36";

const TIMEOUT_MS = 15_000;
const NETWORK_IDLE_TIMEOUT_MS = 10_000;

const detectionConfig: DetectionConfig = buildDetectionConfig({
  KNOWN_DOMAINS,
  MAIN_DOMAIN,
  CARTE_ROUTE,
  FORMULAIRE_ROUTE,
  DECHET_ROUTE,
  CARTE_SCRIPT_FILENAME,
  FORMULAIRE_SCRIPT_FILENAME,
});

// -- URL reading --

function readUrlsFromFile(filePath: string): string[] {
  const content = fs.readFileSync(filePath, "utf-8");
  const ext = path.extname(filePath).toLowerCase();

  if (ext === ".csv") {
    return readUrlsFromCsv(content);
  }

  // Text file: one URL per line
  return content
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith("#"));
}

function readUrlsFromCsv(content: string): string[] {
  const lines = content.split("\n");
  if (lines.length === 0) return [];

  const headers = parseCsvLine(lines[0]);
  const columnIndex = headers.indexOf("Lien carte ou données");

  if (columnIndex === -1) {
    console.error('CSV: colonne "Lien carte ou données" introuvable');
    console.error("Colonnes disponibles:", headers.join(", "));
    process.exit(1);
  }

  const urls: string[] = [];
  for (let i = 1; i < lines.length; i++) {
    const row = parseCsvLine(lines[i]);
    if (row.length > columnIndex) {
      const url = row[columnIndex].trim();
      if (url && url !== "?") {
        urls.push(url);
      }
    }
  }
  return urls;
}

function parseCsvLine(line: string): string[] {
  const fields: string[] = [];
  let current = "";
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (inQuotes) {
      if (char === '"' && line[i + 1] === '"') {
        current += '"';
        i++;
      } else if (char === '"') {
        inQuotes = false;
      } else {
        current += char;
      }
    } else {
      if (char === '"') {
        inQuotes = true;
      } else if (char === ",") {
        fields.push(current);
        current = "";
      } else {
        current += char;
      }
    }
  }
  fields.push(current);
  return fields;
}

// -- Result types --

interface UrlResult {
  url: string;
  integration_type: string;
  integration_path: string;
  integration_url_params: string;
  integration_data_attributes: string;
  integration_iframe_type: string;
  integration_slug: string;
  integration_has_adjacent_script: string;
  integration_has_iframe_resizer: string;
  integration_warnings: string;
  integration_error: string;
}

// -- CSV output --

function escapeCsvField(value: string): string {
  if (value.includes(",") || value.includes('"') || value.includes("\n")) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

function writeResultsCsv(results: UrlResult[], outputPath: string): void {
  const fieldnames = [
    "url",
    "integration_type",
    "integration_path",
    "integration_url_params",
    "integration_data_attributes",
    "integration_iframe_type",
    "integration_slug",
    "integration_has_adjacent_script",
    "integration_has_iframe_resizer",
    "integration_warnings",
    "integration_error",
  ];

  const lines = [fieldnames.join(",")];
  for (const result of results) {
    const row = fieldnames.map((field) =>
      escapeCsvField(result[field as keyof UrlResult] || ""),
    );
    lines.push(row.join(","));
  }

  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, lines.join("\n") + "\n", "utf-8");
}

// -- Processing --

function buildResultFromIframe(url: string, iframe: DetectedIframe): UrlResult {
  return {
    url,
    integration_type: iframe.hasAdjacentScript ? "script+iframe" : "iframe",
    integration_path: iframe.src,
    integration_url_params: "",
    integration_data_attributes: JSON.stringify({
      ...iframe.scriptDataAttributes,
      ...iframe.iframeDataAttributes,
    }),
    integration_iframe_type: iframe.type,
    integration_slug: iframe.slug || "",
    integration_has_adjacent_script: iframe.hasAdjacentScript
      ? "true"
      : "false",
    integration_has_iframe_resizer: iframe.hasIframeResizer ? "true" : "false",
    integration_warnings: iframe.warnings
      .map((w) => `[${w.severity}] ${w.message}`)
      .join(" | "),
    integration_error: "",
  };
}

function buildResultFromScript(url: string, script: DetectedScript): UrlResult {
  return {
    url,
    integration_type: "script",
    integration_path: script.path,
    integration_url_params: JSON.stringify(script.urlParams),
    integration_data_attributes: JSON.stringify(script.dataAttributes),
    integration_iframe_type: "",
    integration_slug: "",
    integration_has_adjacent_script: "",
    integration_has_iframe_resizer: "",
    integration_warnings: "",
    integration_error: "",
  };
}

function buildErrorResult(url: string, error: string): UrlResult {
  return {
    url,
    integration_type: "",
    integration_path: "",
    integration_url_params: "",
    integration_data_attributes: "",
    integration_iframe_type: "",
    integration_slug: "",
    integration_has_adjacent_script: "",
    integration_has_iframe_resizer: "",
    integration_warnings: "",
    integration_error: error,
  };
}

function buildNoIntegrationResult(url: string): UrlResult {
  return {
    url,
    integration_type: "",
    integration_path: "",
    integration_url_params: "",
    integration_data_attributes: "",
    integration_iframe_type: "",
    integration_slug: "",
    integration_has_adjacent_script: "",
    integration_has_iframe_resizer: "",
    integration_warnings: "",
    integration_error: "",
  };
}

// -- Main --

async function main() {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.error(
      "Usage: npx tsx scripts/check_carte_integrations.ts <input_file> <output.csv>",
    );
    console.error("");
    console.error("Input: text file (one URL per line) or CSV");
    process.exit(1);
  }

  const [inputFile, outputFile] = args;

  if (!fs.existsSync(inputFile)) {
    console.error(`Input file not found: ${inputFile}`);
    process.exit(1);
  }

  const urls = readUrlsFromFile(inputFile);
  console.log(`${urls.length} URLs to check`);

  if (urls.length === 0) {
    console.error("No URLs found in input file");
    process.exit(1);
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent: USER_AGENT,
    viewport: { width: 1920, height: 1080 },
    ignoreHTTPSErrors: true,
  });

  // Polyfill for __name helper injected by tsx/esbuild when transforming
  // TypeScript. Without this, page.evaluate() of shared detection functions
  // would fail with "ReferenceError: __name is not defined".
  await context.addInitScript(() => {
    (globalThis as any).__name = (fn: any) => fn;
  });

  const results: UrlResult[] = [];
  let foundCount = 0;

  for (let i = 0; i < urls.length; i++) {
    const url = urls[i];
    const progress = `[${i + 1}/${urls.length}]`;

    try {
      const page = await context.newPage();

      // Navigate with domcontentloaded, then wait briefly for JS
      await page.goto(url, {
        waitUntil: "domcontentloaded",
        timeout: TIMEOUT_MS,
      });

      // Wait for network to settle (with short timeout)
      try {
        await page.waitForLoadState("networkidle", {
          timeout: NETWORK_IDLE_TIMEOUT_MS,
        });
      } catch {
        // If networkidle takes too long, wait a bit for basic JS execution
        await page.waitForTimeout(2000);
      }

      // Run shared detection in page context
      const iframes = await page.evaluate(
        detectIframeIntegrations,
        detectionConfig,
      );
      const scripts = await page.evaluate(
        detectScriptIntegrations,
        detectionConfig,
      );

      await page.close();

      if (iframes.length > 0) {
        // Report each detected iframe as a separate result row
        for (const iframe of iframes) {
          results.push(buildResultFromIframe(url, iframe));
        }
        foundCount++;
        console.log(
          `${progress} ${url} -> ${iframes.length} iframe(s) found (${iframes.map((f) => f.type).join(", ")})`,
        );
      } else if (scripts.length > 0) {
        // Report standalone scripts (not adjacent to iframe)
        for (const script of scripts) {
          results.push(buildResultFromScript(url, script));
        }
        foundCount++;
        console.log(
          `${progress} ${url} -> ${scripts.length} standalone script(s) found`,
        );
      } else {
        results.push(buildNoIntegrationResult(url));
        console.log(`${progress} ${url} -> no integration found`);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      results.push(buildErrorResult(url, errorMsg));
      console.log(`${progress} ${url} -> ERROR: ${errorMsg}`);
    }
  }

  await browser.close();

  // Write results
  writeResultsCsv(results, outputFile);

  console.log("");
  console.log(`Results written to ${outputFile}`);
  console.log(`Integrations found: ${foundCount}/${urls.length}`);
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
