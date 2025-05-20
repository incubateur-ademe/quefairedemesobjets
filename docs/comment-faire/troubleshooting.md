# ☎️ 3615 jaidesproblemes

Une liste de solutions à des situations fréquentes qui peuvent se produire en local, en staging, en prod...

## git
### En cas de conflits sur `.secrets.baseline`
```bash
# installer detect-secrets s'il n'est pas présent dans l'environnement virtuel
# ou en local
poetry add detect-secrets
# re-générer .secrets.baseline
poetry run detect-secrets scan > .secrets.baseline
# ajout au rebase en cours
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

## déploiement du poste developpeur

### Je n'arrive pas a accéder à l'interface via une url *.local

L'interface sur un poste développeur doit-être accessible via les URLs:

- http://quefairedemesdechets.ademe.local/
- http://quefairedemesobjets.ademe.local/
- http://lvao.ademe.local/ : redirigé vers le site institutionnel

Si tel n'est pas le cas, voici quelques configuration à vérifier

#### /etc/hosts

Dans la configuration `/etc/hosts`, vérifier la présence des lignes

```
127.0.0.1       lvao.ademe.local
127.0.0.1       quefairedemesdechets.ademe.local
127.0.0.1       quefairedemesobjets.ademe.local
```

#### Vérifier la présence des certificats ssl

Si les certificats ne sont pas présents, les logs du serveur nginx affichent une erreur type

```
lvao-proxy-1  | 2025/05/20 10:47:25 [emerg] 1#1: cannot load certificate "/etc/nginx/ssl/lvao.ademe.local+1.pem": BIO_new_file() failed (SSL: error:80000002:system library::No such file or directory:calling fopen(/etc/nginx/ssl/lvao.ademe.local+1.pem, r) error:10000080:BIO routines::no such file)
```

Dans ce cas, (re-)générer les certificats

```
make init-certs
```

#### .env

Enfin, vérifier les variables d'environnement en prenant exemple sur le fichier `.env.template`
