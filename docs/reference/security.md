# Sécurité

## Politique de sécurité

La politique de sécurité est consultable ici : [SECURITY.md](../../SECURITY.md)

## Monitoring

### Monitoring de sécurité

Les applications maintenues par la startup sont monitorées par l'application Dashlord disponible ici : [https://dashlord.incubateur.ademe.fr/](https://dashlord.incubateur.ademe.fr/)

### Monitoring de code

les robots suivants sont configurés en CI pour inspecter le code :

- CodeQL : controle de qualité de code
- GitGuardian : detection de mot de passe
- Dependabot : mise à jour des dépendances (1 fois par semaine)
- ruff : respect des standard de code python
- prettier, black : formatage de code

### Monitoring applicatif

L'application est monitorée par l'[instance Sentry de beta.gouv.fr](https://sentry.incubateur.net/organizations/betagouv/projects/que-faire-de-mes-objets/?project=115)
