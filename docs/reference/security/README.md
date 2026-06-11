# Security

## Security policy

The security policy is available here: [SECURITY.md](https://github.com/incubateur-ademe/quefairedemesobjets/blob/main/SECURITY.md)

## Monitoring

### Security monitoring

Applications maintained by the startup are monitored by the Dashlord application available here: [https://dashlord.incubateur.ademe.fr/](https://dashlord.incubateur.ademe.fr/)

### Code monitoring

The following bots are configured in CI to inspect the code:

- CodeQL: code quality checks
- GitGuardian: secret and password detection
- Dependabot: dependency updates (once a week)
- ruff: enforcement of Python code standards
- prettier, black: code formatting

### Application monitoring

The application is monitored by the [beta.gouv.fr Sentry instance](https://sentry.incubateur.net/organizations/betagouv/projects/que-faire-de-mes-objets/?project=115)

For the full observability stack (Sentry, PostHog, Matomo, Scaleway Cockpit, Mattermost, healthcheck), see [Monitoring](../infrastructure/monitoring.md).

## Topics

```{toctree}
:maxdepth: 2

inventory.md
providers.md
authentication.md
network.md
secrets.md
backups.md
pca.md
pra.md
reviews.md
```
