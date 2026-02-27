# iframe-inspector

Outils de detection des integrations iframe/script QFDMO ("Que faire de mes objets") sur des sites tiers.

Ce dossier regroupe :

- **[chrome-extension/](chrome-extension/)** — Extension Chrome qui analyse la page courante et affiche les integrations detectees (type d'iframe, script adjacent, iframe-resizer, warnings).
- **[inspector-script/](inspector-script/)** — Script batch qui inspecte une liste d'URL avec Playwright et produit un rapport CSV.
- **shared/** — Code de detection mutualise entre l'extension et le script (constantes, fonctions de detection).

## Architecture

```
iframe-inspector/
├── chrome-extension/     # Extension Chrome/Firefox
├── inspector-script/     # Script batch Playwright
└── shared/               # Code partage
    ├── constants.ts       # Domaines, routes, noms de fichiers
    └── detection.ts       # Fonctions de detection (iframe + script)
```

Les fonctions de detection dans `shared/detection.ts` sont auto-contenues (tous les helpers definis a l'interieur du corps de la fonction) pour pouvoir etre serialisees et executees dans un contexte navigateur via `page.evaluate()` de Playwright ou dans le content script de l'extension Chrome.
