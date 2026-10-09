/** Minimal client-side router: two screens, every navigation state (filters,
 * page, view…) lives in the URL search params so it can be shared and restored.
 * Kept in-house so that the bundle does not depend on package `exports`
 * resolution, which the project Parcel configuration does not enable. */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type MouseEvent,
  type ReactNode,
} from "react"

export type Route =
  { name: "cohortes" } | { name: "cohorte"; cohorteId: number } | { name: "notFound" }

export type SearchParams = Record<string, string>

type Location = { pathname: string; search: string }

type RouterValue = {
  basepath: string
  route: Route
  search: SearchParams
  navigate: (to: string, options?: { replace?: boolean }) => void
}

const RouterContext = createContext<RouterValue | null>(null)

export function matchRoute(basepath: string, pathname: string): Route {
  const base = basepath.replace(/\/$/, "")
  if (!pathname.startsWith(base)) {
    return { name: "notFound" }
  }
  const path = pathname.slice(base.length).replace(/\/$/, "") || "/"
  if (path === "/") {
    return { name: "cohortes" }
  }
  const cohorte = /^\/cohortes\/(\d+)$/.exec(path)
  if (cohorte) {
    return { name: "cohorte", cohorteId: Number(cohorte[1]) }
  }
  return { name: "notFound" }
}

export function parseSearch(search: string): SearchParams {
  return Object.fromEntries(new URLSearchParams(search))
}

/** Builds an href below the basepath, dropping empty search params. */
export function buildHref(
  basepath: string,
  path: string,
  search: Record<string, string | number | undefined | null> = {},
) {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(search)) {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value))
    }
  }
  const query = params.toString()
  return `${basepath.replace(/\/$/, "")}${path}${query ? `?${query}` : ""}`
}

function currentLocation(): Location {
  return { pathname: window.location.pathname, search: window.location.search }
}

export function RouterProvider({
  basepath,
  children,
}: {
  basepath: string
  children: ReactNode
}) {
  const [location, setLocation] = useState(currentLocation)

  useEffect(() => {
    const onPopState = () => setLocation(currentLocation())
    window.addEventListener("popstate", onPopState)
    return () => window.removeEventListener("popstate", onPopState)
  }, [])

  const navigate = useCallback((to: string, options?: { replace?: boolean }) => {
    if (options?.replace) {
      window.history.replaceState(null, "", to)
    } else {
      window.history.pushState(null, "", to)
    }
    setLocation(currentLocation())
  }, [])

  const value = useMemo(
    () => ({
      basepath,
      route: matchRoute(basepath, location.pathname),
      search: parseSearch(location.search),
      navigate,
    }),
    [basepath, location, navigate],
  )

  return <RouterContext.Provider value={value}>{children}</RouterContext.Provider>
}

export function useRouter(): RouterValue {
  const value = useContext(RouterContext)
  if (!value) {
    throw new Error("useRouter must be used inside <RouterProvider>")
  }
  return value
}

type SearchPatch = Record<string, string | number | undefined | null>

/** Search params of the current page, and a setter merging a patch into them
 * (undefined / empty values are removed from the URL). */
export function useSearchParams() {
  const { search, navigate } = useRouter()
  const setSearch = useCallback(
    (patch: SearchPatch, options?: { replace?: boolean }) =>
      navigate(
        buildHref("", window.location.pathname, { ...search, ...patch }),
        options,
      ),
    [search, navigate],
  )
  return [search, setSearch] as const
}

/** Internal link: plain <a> (open in new tab works), client navigation on click. */
export function Link({
  to,
  className,
  children,
}: {
  to: string
  className?: string
  children: ReactNode
}) {
  const { navigate } = useRouter()
  const onClick = (event: MouseEvent<HTMLAnchorElement>) => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey) {
      return
    }
    event.preventDefault()
    navigate(to)
  }
  return (
    <a href={to} className={className} onClick={onClick}>
      {children}
    </a>
  )
}
