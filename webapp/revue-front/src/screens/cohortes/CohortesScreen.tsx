import { useApp } from "../../context"

/** Screen 1: list of the SOURCE cohortes (increment 3). */
export function CohortesScreen() {
  const { bootstrap } = useApp()
  return (
    <main className="screen">
      <h1>Cohortes SOURCE</h1>
      <p className="muted">Connecté en tant que {bootstrap.user.username}.</p>
    </main>
  )
}
