# 3615 jaidesproblemes

Une liste de solutions à des situations fréquentes qui peuvent se produire en local, en staging, en prod...

## git
### En cas de conflits sur `.secrets.baseline`
```bash
# installer detect-secrets s'il n'est pas présent dans l'environnement virtuel
# ou en local
pip install detect-secrets
# re-générer .secrets.baseline
detect-secrets scan > .secrets.baseline
# ajout au rebase en courts
git add .secrets.baseline
# continuer le rebase si aucun autre conflit n'est présent
git rebase --continue
```

### En cas de conflits sur `poetry.lock`

```bash
# ou avec poetry
rm poetry.lock
poetry lock

git add poetry.lock

# si c'est pendant un rebase...
git rebase --continue
```
