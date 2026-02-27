import { PageAnalysis } from "../../types";

chrome.tabs.onActivated.addListener(async (activeInfo) => {
  await analyzeTab(activeInfo.tabId);
});

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo) => {
  if (changeInfo.status === "complete") {
    await analyzeTab(tabId);
  }
});

async function analyzeTab(tabId: number) {
  try {
    const response = await chrome.tabs.sendMessage(tabId, {
      type: "ANALYZE_PAGE",
    });
    const analysis = response as PageAnalysis;
    updateBadge(tabId, analysis);
  } catch {
    chrome.action.setBadgeText({ text: "", tabId });
  }
}

function updateBadge(tabId: number, analysis: PageAnalysis) {
  if (analysis.totalWarnings > 0) {
    chrome.action.setBadgeText({ text: String(analysis.totalWarnings), tabId });
    chrome.action.setBadgeBackgroundColor({ color: "#e1000f", tabId });
    chrome.action.setBadgeTextColor({ color: "#ffffff", tabId });
  } else if (analysis.iframes.length > 0) {
    chrome.action.setBadgeText({
      text: String(analysis.iframes.length),
      tabId,
    });
    chrome.action.setBadgeBackgroundColor({ color: "#18753c", tabId });
    chrome.action.setBadgeTextColor({ color: "#ffffff", tabId });
  } else {
    chrome.action.setBadgeText({ text: "", tabId });
  }
}
