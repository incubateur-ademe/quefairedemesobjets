# Infrastructure, monitoring, CI/CD

This documentation covers:

- **Provisioning with OpenTofu**: infrastructure resources (compute instances, databases, networks, buckets, etc.) are defined as code in the `infrastructure/` directory and applied using OpenTofu/Terragrunt workflows.
- **Monitoring on Scaleway**: production services run on Scaleway; dashboards, logs, and metrics are available in the Scaleway console to monitor health, performance, and usage.
- **CI/CD with GitHub Actions**: automated pipelines in `.github/workflows/` build, test, and deploy the application, including interactions with Scaleway and the OpenTofu-based infrastructure when needed.

```{toctree}
:maxdepth: 2

provisioning.md
ci-cd.md
monitoring.md
```
