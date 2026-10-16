// MapLibre worker, built apart: Parcel target `worker`, context `web-worker`
// (see package.json).
//
// maplibre-gl 6 resolves its worker through `import.meta.url`, which Parcel
// does not preserve: it needs an explicit URL. Yet this worker imports the
// MapLibre core (480 kB) from a sibling file, and any bundle produced in the
// page context (`bundle-text:`, `url:`) lets Parcel share that core with the
// page. A worker lives in its own context and cannot reach it: "Cannot find
// module", and the map stays grey, no tile ever requested.
//
// Parcel never shares code across contexts: a `web-worker` target yields one
// self-contained file, served and hashed by whitenoise like the others.
// `scopeHoist` is off for that target: with hoisting, maplibre-gl's
// `sideEffects` field lets Parcel drop this entry, which exports nothing, and
// the bundle comes out empty.
import "maplibre-gl/dist/maplibre-gl-worker.mjs"
