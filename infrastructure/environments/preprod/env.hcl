locals {
  # Public hostnames are <service>.<domain> (wildcard CNAME to the gateway)
  domain = "preprod.quefairedemesobjets.ademe.fr"

  # Preprod does not always deploy Metabase. Set this to true only after
  # metabase_db_username is set on the database stack and metabase_containers
  # has been applied. Nginx then exposes metabase.<domain>.
  metabase_enabled = false
}
