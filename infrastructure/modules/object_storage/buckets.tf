# Buckets the applications read and write. They were created by hand: the
# import adopts the ones listed in `import_buckets`, and creates nothing new.
# TODO: drop `import_buckets` once every environment has been applied, so that
# a rebuild from an empty project creates the buckets instead of importing them.

locals {
  buckets = toset(concat(var.critical_buckets, var.other_buckets))
}

import {
  for_each = toset(var.import_buckets)
  to       = scaleway_object_bucket.this[each.key]
  id       = "fr-par/${each.key}"
}

resource "scaleway_object_bucket" "this" {
  for_each = local.buckets

  name = each.key
  acl  = contains(var.public_read_buckets, each.key) ? "public-read" : "private"

  versioning {
    enabled = contains(var.critical_buckets, each.key)
  }

  lifecycle {
    prevent_destroy = true
  }
}
