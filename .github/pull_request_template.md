# Description succincte du problème résolu

Carte Notion : [Titre de la carte](https://notion.so/...)

Description plus détaillée de l'intention, l'approche ou de l'implémentation (ce qui n’est pas visible directement en lisant le code)

<!-- Cocher la/les case.s appropriée.s -->
**Type de changement** :
- [ ] Bug fix
- [ ] Nouvelle fonctionnalité
- [ ] Mise à jour de données / DAG
- [ ] Les changements nécessitent une mise à jour de documentation
- [ ] Refactoring de code (explication à retrouver dans la description)

## Comment tester

En local / staging :
- Récupérer la base de production
- Aller sur http://localhost:8000
- Cliquer sur ABC
- …

## Déploiement

<!-- Dans le cas où il y a des instructions spécifiques de déploiement -->

- Exécuter les migrations
- Exécuter la commande `rf -rf /`
- ...

## Développement local

<!-- Dans le cas où il y a des instructions spécifiques pour garantir un local fonctionnel pour le reste de l'équipe -->
- Mettre à jour le `.env`
- Réinstaller les dépendances Python avec `pip install -r requirements.txt -r dev-requirements.txt`
- Réinstaller les dépendances node avec `npm install`
- Rebuild la stack docker avec `docker compose build`
- ...

## Auto-review

Les trucs à faire avant de demander une review :
- [ ] J'ai bien relu mon code
- [ ] La CI passe bien
- [ ] En cas d'ajout de variable d'environnement, j'ai bien mis à jour le `.env.template`
- [ ] J'ai ajouté des tests qui couvrent le nouveau code
