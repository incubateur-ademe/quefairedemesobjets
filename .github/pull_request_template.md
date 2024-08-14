Description succincte du problème résolu

Explication de l'implémentation (ce qui n’est pas visible directement en lisant le code)

Type de changement :
- [ ] Bug fix
- [ ] Nouvelle fonctionnalité
- [ ] Mise à jour de données / DAG
- [ ] Les changements nécessitent une mise à jour de documentation

## Comment tester
En local / staging :
- Aller sur http://localhost:8000
- Cliquer sur ABC
- …

## Déploiement
- Exécuter les migrations
- Exécuter la commande `rf -rf /`
- ...

## Développement local

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
