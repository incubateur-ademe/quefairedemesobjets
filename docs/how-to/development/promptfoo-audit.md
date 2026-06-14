# Auditer les réponses de l'assistant avec Promptfoo

[Promptfoo](https://www.promptfoo.dev/) est un outil d'évaluation de prompts qui permet de
tester la qualité des réponses de l'assistant « Que faire de mes objets ? » sur plusieurs
modèles de langage (LLM) simultanément.

## Principe

L'audit croise 3 dimensions :

- **prompts** : question seule (`sans-page`) vs question + contenu de la page ADEME
  (`avec-page`)
- **modèles** : Claude, Mistral, Gemini, DeepSeek…
- **pages** : plusieurs catégories d'objets/déchets (meubles, emballages…)

Chaque cellule du tableau produit une note (vert = passe, rouge = échoue) selon des critères
automatiques (mots-clés, rubrique LLM).

## Structure

```
promptfoo-audit/
├── .env.example          # Template des clés API
├── promptfooconfig.yaml  # Configuration : prompts × modèles × tests
├── run.sh                # Lanceur
├── prompts/
│   ├── avec-page.txt     # Prompt avec le contenu de la page
│   └── sans-page.txt     # Prompt témoin (question seule)
└── pages/                # Contenu des pages ADEME (généré, non versionné)
    ├── meubles.txt
    └── emballages-verre.txt
```

## Prérequis

- Promptfoo installé : `npx promptfoo@latest --version`
- Une clé API pour chaque modèle testé (voir `.env.example`)

## Utilisation

1. **Copier le fichier d'environnement**

   ```sh
   cp promptfoo-audit/.env.example promptfoo-audit/.env
   ```

2. **Renseigner les clés API** dans `promptfoo-audit/.env`

3. **Lancer l'audit**

   ```sh
   ./promptfoo-audit/run.sh
   ```

   La première exécution appelle tous les modèles ; les résultats sont mis en cache dans
   `~/.promptfoo/`. Les appels suivants ne rejouent que ce qui a changé.

4. **Visualiser les résultats**

   ```sh
   promptfoo view
   # → http://localhost:15500
   ```

   Les cellules vertes sont celles qui passent tous les critères. Cliquez sur une cellule
   pour voir la réponse complète et le détail des assertions.

## Ajouter une page à auditer

1. Télécharger la page ADEME :
   ```sh
   curl -sL "https://quefairedemesdechets.ademe.fr/categories/..." \
     -o promptfoo-audit/pages/ma-page.html
   ```
2. Extraire le texte (la commande `python3` utilisée dans `promptfoo-audit/pages/` fait ce
   travail).
3. Ajouter une entrée dans la section `tests` de `promptfooconfig.yaml` avec la question,
   le fichier page et les assertions adaptées.

## Ajouter un modèle

1. Ajouter le provider dans `promptfooconfig.yaml` (ex. `deepseek:deepseek-chat`)
2. Ajouter la variable d'environnement dans `.env.example` et `run.sh`
3. Créer la clé API correspondante

## Remarques

- Le juge des rubriques LLM (`llm-rubric`) utilise Claude Sonnet. La clé `ANTHROPIC_KEY`
  est donc toujours requise, même si vous commentez les autres providers.
- Les fichiers `results.json`, le dossier `pages/` et le fichier `.env` sont ignorés par
  git. Seuls la configuration, les prompts et le lanceur sont versionnés.
