import { useRouter } from "./router"
import { CohorteScreen } from "./screens/cohorte/CohorteScreen"
import { CohortesScreen } from "./screens/cohortes/CohortesScreen"

export function Routes() {
  const { route } = useRouter()
  return (
    <div className="app">
      {route.name === "cohortes" && <CohortesScreen />}
      {route.name === "cohorte" && <CohorteScreen cohorteId={route.cohorteId} />}
      {route.name === "notFound" && (
        <main className="screen">
          <h1>Page introuvable</h1>
        </main>
      )}
    </div>
  )
}
