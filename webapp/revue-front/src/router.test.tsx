import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"

import {
  buildHref,
  Link,
  matchRoute,
  parseSearch,
  RouterProvider,
  useRouter,
} from "./router"

describe("matchRoute", () => {
  it.each([
    ["/data/revue/", { name: "cohortes" }],
    ["/data/revue", { name: "cohortes" }],
    ["/data/revue/cohortes/12", { name: "cohorte", cohorteId: 12 }],
    ["/data/revue/cohortes/12/", { name: "cohorte", cohorteId: 12 }],
    ["/data/revue/cohortes/abc", { name: "notFound" }],
    ["/autre/", { name: "notFound" }],
  ])("%s", (pathname, expected) => {
    expect(matchRoute("/data/revue/", pathname)).toEqual(expected)
  })
})

describe("search params", () => {
  it("builds an href without empty params", () => {
    expect(
      buildHref("/data/revue/", "/cohortes/3", { vue: "lignes", page: 2, filtre: "" }),
    ).toBe("/data/revue/cohortes/3?vue=lignes&page=2")
  })

  it("round-trips a JSON filter", () => {
    const filtre = JSON.stringify({ op: "and", conditions: [] })
    const href = buildHref("/data/revue/", "/", { filtre })
    expect(parseSearch(href.split("?")[1])).toEqual({ filtre })
  })
})

function Where() {
  const { route, search } = useRouter()
  return (
    <p>
      {route.name} {search.vue}
    </p>
  )
}

describe("RouterProvider", () => {
  it("navigates on link click and keeps the search params", async () => {
    window.history.replaceState(null, "", "/data/revue/")
    render(
      <RouterProvider basepath="/data/revue/">
        <Where />
        <Link to="/data/revue/cohortes/7?vue=lignes">aller</Link>
      </RouterProvider>,
    )
    expect(screen.getByText("cohortes")).toBeInTheDocument()

    await userEvent.click(screen.getByText("aller"))

    expect(screen.getByText("cohorte lignes")).toBeInTheDocument()
    expect(window.location.pathname).toBe("/data/revue/cohortes/7")
  })
})
