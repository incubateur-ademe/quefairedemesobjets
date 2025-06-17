// Styles
// These are used by Parcel to generate a css file with
// the same filename as the current .ts file.
// If several .css files are imported here, they will generate
// a single qfdmo.css file.
import "./styles/qfdmo.css"
// Third-party scripts
import "@gouvfr/dsfr/dist/dsfr.module.js"

// Carte scripts.
// This script lives in a different file because it is imported in qfdmd.ts
// as well.
// The current qfdmo.ts file cannot be imported as-is in qfdmd.ts because it
// includes dsfr css and js.
// Once this project will use django-dsfr, the current script
// could be deprecated.
import "./js/carte"
