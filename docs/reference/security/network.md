# Sécurité réseau

Mesures de sécurité au niveau réseau et flux applicatifs.

> **Voir aussi** : [Architecture applicative](../architecture/README.md), [Authentification](authentication.md), [Provisioning](../infrastructure/provisioning.md).

- **Aucun VPC** : les bases de données et containers Scaleway sont exposés publiquement, l'accès est restreint par `sslmode=require` et l'authentification credentials.
- **Registry privé** (`ns-qfdmo`) avec pull authentifié par les Serverless Containers.
- **Limite de débit** dans le nginx placé devant la webapp (`servers.conf.erb`), par adresse IP (dernière entrée de `X-Forwarded-For`, ajoutée par l'hébergeur) : 5 requêtes par minute sur `/admin/login/` et `/cms/login/` (rafale de 10), 10 requêtes par seconde sur `/api/` (rafale de 50). Au-delà : réponse 429. Chaque instance nginx compte de son côté.
- **CORS** géré par `django-cors-headers` côté webapp (origins configurés par environnement).
- **Embeds iframe** : détection par header `Sec-Fetch-Dest: iframe`, header `Vary: Sec-Fetch-Dest` pour différencier les caches. Backlinks contrôlés via `EmbedSettings` (Wagtail).
- **TLS** : terminé par Scalingo (Let's Encrypt) côté webapp, par Scaleway côté Airflow. En local, mkcert + nginx (`nginx-local-only/`).

## Revue des règles de filtrage

Une fois par an (cf. [`reviews.md`](reviews.md)) :

1. Comparer les origines CORS autorisées et les sites autorisés en iframe (`EmbedSettings` dans Wagtail) avec les réutilisations en cours, retirer celles qui ont cessé.
2. Vérifier que les accès aux bases restent limités aux conteneurs et personnes qui en ont besoin.
3. Vérifier que les limites de débit restent adaptées (réponses 429 dans les journaux du nginx).
4. Consigner la revue dans [`reviews.md`](reviews.md) §Règles de filtrage.
