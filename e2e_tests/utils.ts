export async function hideDjangoToolbar(page) {
  await page.locator("#djHideToolBarButton").click()
}
