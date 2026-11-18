// MapLibre worker, built as its own Parcel target (`worker`, context
// `web-worker`, see package.json): maplibre-gl resolves its worker through
// `import.meta.url`, which Parcel drops, and a worker bundled in the page
// context would import a core it cannot reach. `scopeHoist` is off for this
// target, or the side-effect-only import below is dropped.
import "maplibre-gl/dist/maplibre-gl-worker.mjs"
