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
  # base: canonical domain (BASE_URL). gateway: served by the gateway until
  # the DNS switch, under the existing wildcard CNAME. aliases: other domains
  # still pointing at the webapp.
  webapp_base_domain    = "quefairedemesdechets.incubateur.ademe.dev"
  webapp_gateway_domain = "webapp.${local.domain}"
  webapp_alias_domains = [
    "lvao.incubateur.ademe.dev",
    "quefairedemesobjets.incubateur.ademe.dev",
  ]

  # The gateway also serves the previews at https://pr-<n>.<preview_domain>,
  # with webapp_enabled only. Set it once the wildcard CNAME
  # *.<preview_domain> points at the gateway (output domain_name of
  # nginx_containers). Empty: previews only on their Scaleway address.
  # Candidate, not decided yet: preview.quefairedemesdechets.fr
  preview_domain = ""
}
