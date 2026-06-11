# Sécurité réseau

Mesures de sécurité au niveau réseau et flux applicatifs.

> **Voir aussi** : [Architecture applicative](../architecture/README.md), [Authentification](authentication.md), [Provisioning](../infrastructure/provisioning.md).

- **Aucun VPC** : les bases de données et containers Scaleway sont exposés publiquement, l'accès est restreint par `sslmode=require` et l'authentification credentials.
- **Registry privé** (`ns-qfdmo`) avec pull authentifié par les Serverless Containers.
- **CORS** géré par `django-cors-headers` côté webapp (origins configurés par environnement).
- **Embeds iframe** : détection par header `Sec-Fetch-Dest: iframe`, header `Vary: Sec-Fetch-Dest` pour différencier les caches. Backlinks contrôlés via `EmbedSettings` (Wagtail).
- **TLS** : terminé par Scalingo (Let's Encrypt) côté webapp, par Scaleway côté Airflow. En local, mkcert + nginx (`nginx-local-only/`).
