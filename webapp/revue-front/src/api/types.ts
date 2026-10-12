import type { components } from "./schema"

type Schemas = components["schemas"]

export type Cohorte = Schemas["CohorteOut"]
export type CohortePage = Schemas["CohortePageOut"]
export type Compteurs = Schemas["CompteursOut"]
export type LogsCount = Schemas["LogsCountOut"]
export type FilterField = Schemas["FilterFieldOut"]
export type Log = Schemas["LogOut"]
export type LogPage = Schemas["LogPageOut"]
export type CohorteDetail = Schemas["CohorteDetailOut"]
export type Policy = Schemas["PolicyOut"]
export type Groupe = Schemas["GroupeOut"]
export type GroupePage = Schemas["GroupePageOut"]
export type Ligne = Schemas["LigneOut"]
export type Cell = Schemas["CellOut"]
export type Stats = Schemas["StatsOut"]
export type LigneCapacites = Schemas["LigneCapacitesOut"]

export type Modele = "RevisionActeur" | "ParentRevisionActeur"
export type Vue = "groupes" | "lignes"
export type Afficher = "avalider" | "tout"
