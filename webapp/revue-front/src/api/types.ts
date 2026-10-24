import type { components } from "./schema"

type Schemas = components["schemas"]

export type Cohorte = Schemas["CohorteOut"]
export type CohortePage = Schemas["CohortePageOut"]
export type Compteurs = Schemas["CompteursOut"]
export type LogsCount = Schemas["LogsCountOut"]
export type FilterField = Schemas["FilterFieldOut"]
export type Log = Schemas["LogOut"]
export type LogPage = Schemas["LogPageOut"]
