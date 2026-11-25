# Security

## Security policy

The security policy is available here: [SECURITY.md](https://github.com/incubateur-ademe/quefairedemesobjets/blob/main/SECURITY.md)

Incident handling, from detection to post-incident analysis: see [Gestion des incidents de sécurité](incidents.md).

## Monitoring

### Security monitoring

Applications maintained by the startup are monitored by the Dashlord application available here: [https://dashlord.incubateur.ademe.fr/](https://dashlord.incubateur.ademe.fr/)

### Code monitoring

The following bots are configured in CI to inspect the code:

- CodeQL: code quality checks
- GitGuardian: secret and password detection
- Dependabot: dependency updates (once a week)
- Trivy: scan of the Docker images at build time, blocking fixable CRITICAL and HIGH vulnerabilities

Patch delays by severity and end-of-life tracking: see [Maintien en conditions opérationnelles et de sécurité](mco-mcs.md).

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
mco-mcs.md
incidents.md
reviews.md
```
