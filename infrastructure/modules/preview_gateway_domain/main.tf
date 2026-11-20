# The gateway serves every preview from one server block: Scaleway only needs
# each host attached to issue its certificate (HTTP-01, wildcard CNAME). The
# gateway is looked up, not read from its state, which never sees these
# domains.
data "scaleway_container_namespace" "gateway" {
  count = var.domain == "" ? 0 : 1
  name  = var.gateway_namespace
}

data "scaleway_container" "gateway" {
  count        = var.domain == "" ? 0 : 1
  namespace_id = data.scaleway_container_namespace.gateway[0].id
  name         = var.gateway_container
}

resource "scaleway_container_domain" "preview" {
  count        = var.domain == "" ? 0 : 1
  container_id = data.scaleway_container.gateway[0].id
  hostname     = "${var.environment}.${var.domain}"
}
