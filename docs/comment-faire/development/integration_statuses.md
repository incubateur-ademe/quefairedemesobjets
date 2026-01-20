# Vérification du statut des intégrations de la carte

Ce document explique comment utiliser le script `check_carte_integrations.py` pour détecter automatiquement les intégrations de la carte sur les sites web listés dans un CSV.

## Vue d'ensemble

Le script `scripts/check_carte_integrations.py` analyse les pages web listées dans un fichier CSV pour détecter les intégrations de la carte via :

- **Script** : Tags `<script>` avec `src` pointant vers un des domaines valides
- **Iframe** : Tags `<iframe>` avec `src` pointant vers un des domaines valides

Le script extrait les informations suivantes :

- Le type d'intégration (script ou iframe)
- Le chemin relatif du script/iframe
- Les paramètres URL passés dans le `src`
- Les attributs `data-*` du script (pour les intégrations par script uniquement)

## Installation

### Dépendances de base

Les dépendances suivantes sont déjà présentes dans le projet :

- `requests` : Pour les requêtes HTTP
- `beautifulsoup4` : Pour le parsing HTML
- `tqdm` : Pour la barre de progression

### Installation de Playwright (recommandé)

Pour analyser les pages React/JavaScript qui chargent le contenu dynamiquement, il est recommandé d'installer Playwright :

```bash
# Installer la bibliothèque Python
uv add playwright

# Installer les navigateurs (nécessaire une seule fois)
uv run playwright install chromium
```

**Note** : Le script fonctionne sans Playwright, mais ne pourra pas analyser les pages qui nécessitent l'exécution de JavaScript pour charger le contenu.

## Utilisation

### Format du CSV d'entrée

Le CSV doit contenir une colonne nommée `"Lien carte ou données"` qui contient les URLs à analyser.
Le script est conçu pour fonctionner avec l'export en CSV de la page notions qui liste les intégrations : [Réutilisations iFrames et données](https://www.notion.so/accelerateur-transition-ecologique-ademe/7742a21fa14342e9abe0147a18ad1086?v=05e3cb93a7a24636a64bb30e728d411f&source=copy_link)

**Exemple de CSV** :

```csv
Nom,Lien carte ou données,Autre colonne
Site A,https://example.com/carte,...
Site B,https://example.org/map,...
```

### Exécution du script

```bash
uv run python scripts/check_carte_integrations.py input.csv output.csv
```

**Arguments** :

- `input_csv` : Chemin vers le fichier CSV d'entrée
- `output_csv` : Chemin vers le fichier CSV de sortie

### Options avancées

Le script accepte les paramètres suivants via les variables d'environnement ou la modification du code :

- **Timeout** : Par défaut 10 secondes par page. Modifiable dans la fonction `fetch_page_content()`.
- **User-Agent** : Par défaut un User-Agent Chrome standard. Modifiable dans la constante `USER_AGENT`.

## Format de sortie

Le CSV de sortie contient les colonnes suivantes :

| Colonne                       | Description                                                       |
| ----------------------------- | ----------------------------------------------------------------- |
| `url`                         | L'URL analysée (pour permettre le pivot avec le fichier original) |
| `integration_type`            | Type d'intégration : `"script"`, `"iframe"` ou vide si non trouvé |
| `integration_path`            | Chemin relatif du script/iframe (ex: `/static/carte.js`)          |
| `integration_url_params`      | Paramètres URL au format JSON (ex: `{"limit": ["50"]}`)           |
| `integration_data_attributes` | Attributs `data-*` au format JSON (uniquement pour les scripts)   |
| `integration_error`           | Message d'erreur si l'analyse a échoué                            |

**Exemple de sortie** :

```csv
url,integration_type,integration_path,integration_url_params,integration_data_attributes,integration_error
https://example.com/carte,script,/static/carte.js,"{""limit"": [""50""]}","{""action_list"": ""reparer|donner"", ""epci_codes"": ""241400555""}",
https://example.org/map,iframe,/carte,"{""iframe"": [""1""]}",,
https://example.net/page,,,,"Timeout après 10s"
```

## Domaines détectés

Le script détecte les intégrations pour les domaines suivants :

- `lvao.ademe.fr`
- `quefairedemesdechets.ademe.fr`
- `quefairedemesdechets.fr`
- `quefairedemesobjets.ademe.fr`
- `quefairedemesobjets.fr`

## Fonctionnement technique

### Détection des intégrations

1. **Script** : Le script cherche les tags `<script>` avec un attribut `src` contenant l'un des domaines valides. Il extrait :
   - Le chemin relatif via `urllib.parse`
   - Les paramètres URL via `urllib.parse.parse_qs`
   - Tous les attributs `data-*` du script

2. **Iframe** : Si aucun script n'est trouvé, le script cherche les tags `<iframe>` avec un attribut `src` contenant l'un des domaines valides. Il extrait :
   - Le chemin relatif via `urllib.parse`
   - Les paramètres URL via `urllib.parse.parse_qs`

**Note** : Les iframes ne sont recherchées que si aucun script n'est trouvé, pour éviter les doublons (car les scripts génèrent souvent des iframes).

### Gestion des pages JavaScript

Le script utilise deux méthodes selon la disponibilité de Playwright :

1. **Avec Playwright** (recommandé) :
   - Lance un navigateur Chromium headless
   - Navigue vers la page et attend que le JavaScript s'exécute
   - Attend que le réseau soit stable (`networkidle`)
   - Récupère le HTML après exécution du JavaScript

2. **Sans Playwright** (fallback) :
   - Utilise `requests` pour récupérer le HTML initial
   - Ne peut pas exécuter JavaScript
   - Fonctionne uniquement pour les pages statiques

### Gestion des erreurs

Le script gère automatiquement :

- **Timeouts** : Les pages qui prennent trop de temps sont ignorées avec un message d'erreur
- **Erreurs SSL** : Les certificats auto-signés ou invalides sont ignorés (pas de warning)
- **Erreurs HTTP** : Les erreurs de connexion sont capturées et loggées
- **Erreurs Playwright** : En cas d'erreur Playwright, le script bascule automatiquement sur `requests`

### Logging

Le script affiche :

- Le nombre d'URLs trouvées dans le CSV
- La progression avec une barre `tqdm`
- Les warnings pour les erreurs (timeout, erreurs HTTP, etc.)
- Un résumé final avec le nombre d'intégrations trouvées

## Exemples d'utilisation

### Analyser un fichier CSV

```bash
uv run python scripts/check_carte_integrations.py \
  "/path/to/input.csv" \
  "/path/to/output.csv"
```

### Vérifier une seule URL (modification du script)

Pour tester une seule URL, vous pouvez modifier temporairement le script :

```python
# Dans la fonction main(), remplacer process_csv par :
result = check_integration("https://example.com/carte")
print(json.dumps(result, indent=2))
```

## Dépannage

### Playwright non disponible

Si vous voyez le warning :

```
Playwright non disponible. Les pages JavaScript ne seront pas exécutées.
```

Installez Playwright avec :

```bash
uv add playwright
uv run playwright install chromium
```

### Erreurs SSL

Les erreurs SSL sont automatiquement ignorées. Si vous voyez encore des warnings, vérifiez que `urllib3.disable_warnings()` est bien appelé au début du script.

### Timeouts fréquents

Si beaucoup de pages timeout :

1. Augmentez le timeout dans la fonction `fetch_page_content()` (par défaut 10 secondes)
2. Vérifiez votre connexion internet
3. Certaines pages peuvent être très lentes à charger

### Pages React non détectées

Si une page React ne détecte pas l'intégration :

1. Vérifiez que Playwright est installé
2. Augmentez le timeout pour laisser plus de temps au JavaScript
3. Vérifiez manuellement que l'intégration est bien présente sur la page

## Limitations

- Le script ne peut pas analyser les pages qui nécessitent une authentification
- Les pages avec des protections anti-bot peuvent bloquer le script
- Les pages très lentes peuvent timeout même avec Playwright
- Le script ne suit pas les redirections JavaScript (seulement les redirections HTTP)
