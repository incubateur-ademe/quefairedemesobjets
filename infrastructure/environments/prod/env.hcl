locals {
  # Public hostnames are <service>.<domain> (wildcard CNAME to the gateway)
  domain = "quefairedemesobjets.ademe.fr"

  metabase_enabled = true

  # The gateway serves the webapp from servers.conf.erb. Set this to true only
  # once webapp_container has been applied: the gateway stack reads its
  # outputs, and every release applies the gateway.
  webapp_enabled = false

  # ENVIRONMENT of the webapp, the exact value templates/admin/base.html and
  # servers.conf.erb test.
  webapp_environment = "production"

  # Host names of the webapp, the only ones Django accepts (ALLOWED_HOSTS).
  # base: canonical domain (BASE_URL). aliases: other domains still pointing
  # at the webapp.
  webapp_base_domain = "quefairedemesdechets.ademe.fr"
  webapp_alias_domains = [
    "lvao.ademe.fr",
    "quefairedemesobjets.ademe.fr",
    "longuevieauxobjets.ademe.fr",
    "quefairedemesobjets.fr",
    "quefairedemesdechets.fr",
  ]
}
