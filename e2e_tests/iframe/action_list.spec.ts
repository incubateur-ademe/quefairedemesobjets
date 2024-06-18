import { expect, test } from "@playwright/test"

test("Action list by default", async ({ page }) => {
    await page.goto(`http://localhost:8000/?iframe`, {
        waitUntil: "networkidle",
    })

    const id_action_list1 = await page.$eval("#id_action_list", (el) => el.value)
    expect(id_action_list1).toBe(
        "preter|emprunter|louer|mettreenlocation|reparer|donner|echanger|acheter|revendre",
    )
})

test("Action list is well set with jai", async ({ page }) => {
    await page.goto(`http://localhost:8000/?iframe&direction=jai&action_list=preter`, {
        waitUntil: "networkidle",
    })

    const id_action_list1 = await page.$eval("#id_action_list", (el) => el.value)
    expect(id_action_list1).toBe("preter")

    // Select "jai" option
    await page.check("#jai")

    // Assuming "action1" and "action2" are ids of checkboxes inside "jaiTarget"
    // Check these checkboxes
    await page.click('label[for="jai_reparer"]')

    // Expect id_action_list to be "reparer"
    const id_action_list2 = await page.$eval("#id_action_list", (el) => el.value)
    expect(id_action_list2).toBe("preter|reparer")
})

test("Action list is well set with jecherche", async ({ page }) => {
    await page.goto(
        `http://localhost:8000/?iframe&direction=jecherche&action_list=emprunter`,
        {
            waitUntil: "networkidle",
        },
    )

    // check that the action list is well set by default
    const id_action_list1 = await page.$eval("#id_action_list", (el) => el.value)
    expect(id_action_list1).toBe("emprunter")

    // Assuming "action1" and "action2" are ids of checkboxes inside "jaiTarget"
    // Check these checkboxes
    await page.click('label[for="jecherche_emprunter"]')
    await page.click('label[for="jecherche_louer"]')

    // Expect id_action_list to be "reparer"
    const id_action_list2 = await page.$eval("#id_action_list", (el) => el.value)
    expect(id_action_list2).toBe("louer")
})
