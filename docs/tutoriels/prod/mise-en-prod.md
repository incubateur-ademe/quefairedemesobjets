# 🚀 Mise en production - OBSOLETE, à mettre à jour


1. Créer un tag depuis l'interface GitHub ou la ligne de commande
```
git checkout main
git reset --hard origin/main
git tag v1.x.y
git push --tags
```
On en profite au passage pour s'assurer que notre branche main est bien iso avec celle du dépôt distant.

2. Cela va déclencher une action GitHub, qui va automatiquement créer la release
3. Une fois la release créée, celle-ci peut être modifiée pour adapter son contenu à la teneur des changements déployés
4. L'équipe doit être prévenue sur le [canal équipe](https://mattermost.incubateur.net/betagouv/channels/longuevieauxobjets-equipe)
