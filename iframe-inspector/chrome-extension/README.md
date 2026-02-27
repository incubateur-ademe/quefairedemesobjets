# chrome-extension

Extension Chrome pour detecter et analyser les integrations iframe/script QFDMO sur la page courante.

## Fonctionnalites

- Detection des iframes QFDMO (assistant, carte, carte sur mesure, carte preconfiguree)
- Verification de la presence d'un script adjacent et d'iframe-resizer
- Affichage des attributs `data-*` configures
- Avertissements sur la configuration (domaine non principal, script manquant, etc.)
- Lecture des donnees de session storage sur les pages QFDMO

## Developpement

```bash
cd iframe-inspector/chrome-extension
npm install
npm run dev          # build + watch (Chrome)
npm run dev:firefox  # build + watch (Firefox)
```

## Build

```bash
npm run build          # build production Chrome
npm run build:firefox  # build production Firefox
```

## Charger l'extension

### Chrome

1. Ouvrir [chrome://extensions](chrome://extensions)
2. Activer le mode developpeur
3. Cliquer sur "Charger l'extension non empaquetee"
4. Selectionner le dossier `dist_chrome`

### Firefox

1. Ouvrir [about:debugging#/runtime/this-firefox](about:debugging#/runtime/this-firefox)
2. Cliquer sur "Charger un module temporaire"
3. Selectionner un fichier dans le dossier `dist_firefox` (ex: `manifest.json`)

## Architecture

L'extension utilise les fonctions de detection partagees definies dans `../shared/detection.ts`. Le content script (`src/pages/content/index.tsx`) injecte un probe pour verifier la presence d'iframe-resizer, puis execute la detection partagee.

### Pages

- **popup** (`src/pages/popup/`) — Interface principale affichant les resultats de detection
- **content** (`src/pages/content/`) — Content script injecte dans chaque page pour la detection
- **background** (`src/pages/background/`) — Service worker

### Technologies

- React 19, TypeScript, Tailwind CSS 4
- Vite + @crxjs/vite-plugin
- Manifest V3
