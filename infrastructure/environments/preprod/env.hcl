locals {
  # Preprod does not always deploy Metabase. Set this to true only after
  # metabase_db_username is set on the database stack and metabase_containers
  # has been applied. Nginx then exposes metabase.preprod.quefairedemesobjets.ademe.fr.
  metabase_enabled = false
}
