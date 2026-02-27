# inspector-script

Script batch pour detecter les integrations iframe/script QFDMO sur une liste d'URL. Il utilise Playwright pour charger chaque page et execute les fonctions de detection partagees avec l'extension Chrome.

## Installation

```bash
cd iframe-inspector/inspector-script
npm install
npx playwright install chromium
```

## Utilisation

```bash
npx tsx check_carte_integrations.ts <fichier_entree> <fichier_sortie.csv>
```

### Formats d'entree

- **Fichier texte** : une URL par ligne (les lignes commencant par `#` sont ignorees)
- **Fichier CSV** : les URL sont lues depuis la colonne `Lien carte ou donnees`

### Exemple

```bash
npx tsx check_carte_integrations.ts ../../scripts/list-reuse-url.txt output.csv
```

## Sortie CSV

Le fichier CSV genere contient une ligne par integration detectee avec les colonnes suivantes :

| Colonne                           | Description                                                                     |
| --------------------------------- | ------------------------------------------------------------------------------- |
| `url`                             | URL de la page inspectee                                                        |
| `integration_type`                | Type d'integration : `script+iframe`, `iframe`, `script`                        |
| `integration_path`                | URL source de l'iframe ou chemin du script                                      |
| `integration_url_params`          | Parametres URL du script (JSON)                                                 |
| `integration_data_attributes`     | Attributs `data-*` du script et/ou de l'iframe (JSON)                           |
| `integration_iframe_type`         | Type d'iframe : `assistant`, `carte`, `carte_sur_mesure`, `carte_preconfiguree` |
| `integration_slug`                | Slug de la carte sur mesure (si applicable)                                     |
| `integration_has_adjacent_script` | `true` si un script QFDMO est adjacent a l'iframe                               |
| `integration_has_iframe_resizer`  | `true` si iframe-resizer est detecte                                            |
| `integration_warnings`            | Avertissements de configuration                                                 |
| `integration_error`               | Message d'erreur si la page n'a pas pu etre chargee                             |

Si aucune integration n'est detectee sur une page, une ligne est quand meme generee avec uniquement l'URL renseignee.
