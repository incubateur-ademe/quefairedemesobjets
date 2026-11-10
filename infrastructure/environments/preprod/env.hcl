locals {
  # Public hostnames are <service>.<domain> (wildcard CNAME to the gateway)
  domain = "preprod.quefairedemesobjets.ademe.fr"

  # Preprod does not always deploy Metabase. Set this to true only after
  # metabase_db_username is set on the database stack and metabase_containers
  # has been applied. Nginx then exposes metabase.<domain>.
  metabase_enabled = false

  # The gateway serves the webapp from servers.conf.erb. Set this to true only
  # once webapp_container has been applied: the gateway stack reads its
  # outputs, and every push to main applies the gateway.
  webapp_enabled = false

  # ENVIRONMENT of the webapp: "staging" and not "preprod", templates/admin/base.html
  # and servers.conf.erb test this exact value.
  webapp_environment = "staging"

  # Host names of the webapp, the only ones Django accepts (ALLOWED_HOSTS).
  # base: canonical domain (BASE_URL). aliases: other domains still pointing
  # at the webapp.
  webapp_base_domain = "quefairedemesdechets.incubateur.ademe.dev"
  webapp_alias_domains = [
    "lvao.incubateur.ademe.dev",
    "quefairedemesobjets.incubateur.ademe.dev",
  ]
}
