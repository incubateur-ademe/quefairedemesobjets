// Worker MapLibre, construit à part : cible Parcel `worker`, contexte
// `web-worker` (voir package.json).
//
// maplibre-gl 6 résout son worker via `import.meta.url`, que Parcel ne conserve
// pas : il faut lui fournir une URL. Or ce worker importe le cœur de MapLibre
// (480 ko) depuis un fichier voisin, et tout bundle produit dans le contexte de
// la page — `bundle-text:`, `url:` — laisse Parcel partager ce cœur avec elle.
// Un worker vit dans son propre contexte et ne peut pas l'atteindre : « Cannot
// find module », et la carte reste grise, sans aucune tuile demandée.
//
// Parcel ne partage jamais de code entre contextes : une cible `web-worker`
// donne un seul fichier autonome, que whitenoise sert et hache comme les autres.
import "maplibre-gl/dist/maplibre-gl-worker.mjs"
