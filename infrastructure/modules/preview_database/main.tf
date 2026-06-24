data "scaleway_rdb_instance" "host" {
  instance_id = var.webapp_instance_id
}

resource "random_password" "preview" {
  length  = 32
  special = true
  # Scaleway RDB requires at least one special char, digit, lowercase and
  # uppercase letter. Restricted to chars that don't need URL-encoding in
  # the postgres:// DSN built below (no @, :, /, ?, #, %).
  override_special = "-_.~!*"
  min_special      = 1
  min_numeric      = 1
  min_lower        = 1
  min_upper        = 1
}

locals {
  host = data.scaleway_rdb_instance.host.load_balancer.0.ip
  port = data.scaleway_rdb_instance.host.load_balancer.0.port

  # var.webapp_instance_id is the Terraform-style composite ID
  # ("fr-par/<uuid>"); the scw CLI's instance-id argument wants the bare
  # UUID only.
  instance_uuid = element(split("/", var.webapp_instance_id), length(split("/", var.webapp_instance_id)) - 1)

  preview_db_url = format(
    "postgresql://%s:%s@%s:%s/%s?sslmode=require", # pragma: allowlist secret
    var.preview_db_username,
    random_password.preview.result,
    local.host,
    local.port,
    var.preview_db_name,
  )
}

# Database, user and privilege are managed via the `scw` CLI instead of the
# scaleway_rdb_database/user/privilege Terraform resources: the provider hit
# a "Missing Resource Identity After Read" bug on scaleway_rdb_privilege once
# the database had been reseeded a few times, and separately the privilege
# grant silently never took effect (the user ended up with permission=none
# on its own database). The CLI calls the same Scaleway API directly and
# sidesteps both issues.
#
# Re-runs on every deploy (image_tag changes each push): delete-if-exists +
# recreate gives a guaranteed fresh database every time, matching the
# project's existing restore pattern (see scripts/restore_sample_locally.sh,
# restore_prod_locally.sh, restore_prod_to_preprod.sh) of dropping tables
# individually, creating extensions BEFORE restoring, and passing --no-acl
# on both pg_dump and pg_restore so the dump carries no ACL/REVOKE
# statements that could revoke the preview user's own CONNECT privilege.
resource "null_resource" "seed_from_sample" {
  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]
    environment = {
      INSTANCE_ID                  = local.instance_uuid
      DB_NAME                      = var.preview_db_name
      DB_USERNAME                  = var.preview_db_username
      DB_PASSWORD                  = random_password.preview.result
      PREVIEW_DB_URL               = local.preview_db_url
      EXTENSIONS_SCRIPT            = var.create_extensions_script_path
      WAGTAIL_FRENCH_CONFIG_SCRIPT = var.create_wagtail_french_config_script_path
      IMAGE_TAG                    = var.image_tag
    }
    command = <<-EOT
      set -euo pipefail

      scw rdb database delete instance-id="$INSTANCE_ID" name="$DB_NAME" 2>/dev/null || true
      scw rdb database create instance-id="$INSTANCE_ID" name="$DB_NAME"

      # `user create` on an already-existing name doesn't error, but
      # also silently does NOT update the password (confirmed: its
      # output omits the password and the new one doesn't authenticate).
      # `user update` is the one that actually resyncs it.
      if scw rdb user list instance-id="$INSTANCE_ID" -o json \
           | grep -q "\"name\":\"$DB_USERNAME\""; then
        scw rdb user update instance-id="$INSTANCE_ID" name="$DB_USERNAME" \
          password="$DB_PASSWORD"
      else
        scw rdb user create instance-id="$INSTANCE_ID" name="$DB_USERNAME" \
          password="$DB_PASSWORD" generate-password=false is-admin=false
      fi

      scw rdb privilege set instance-id="$INSTANCE_ID" \
        database-name="$DB_NAME" user-name="$DB_USERNAME" permission=all

      for table in $(psql "$PREVIEW_DB_URL" -t -c "SELECT tablename FROM pg_tables WHERE schemaname='public'"); do
        psql "$PREVIEW_DB_URL" -c "DROP TABLE IF EXISTS \"$table\" CASCADE;"
      done
      psql "$PREVIEW_DB_URL" -f "$EXTENSIONS_SCRIPT"
      psql "$PREVIEW_DB_URL" -f "$WAGTAIL_FRENCH_CONFIG_SCRIPT"

      # Dump the sample database to a temp file.
      # If the sample DB is unreachable, warn but continue — previews can
      # still serve as infrastructure smoke tests without seeded data.
      DUMP_FILE="$(mktemp)"
      RESTORE_LOG="$(mktemp)"
      if pg_dump -Fc --no-acl --no-owner --no-privileges "$SAMPLE_DB_URI" > "$DUMP_FILE" 2>/dev/null; then
        # --clean emits DROP/ALTER for objects it assumes exist; against
        # the freshly emptied database those pre-drops fail with exit 1.
        # That's benign — but anything above 1 is a real restore error.
        set +e
        pg_restore -d "$PREVIEW_DB_URL" \
            --schema=public --no-acl --no-owner --no-privileges \
            "$DUMP_FILE" > "$RESTORE_LOG" 2>&1
        RESTORE_RC=$?
        set -e

        # Show restore errors (first 30 lines)
        if grep -i 'error' "$RESTORE_LOG" | head -30; then
          echo "--- pg_restore errors above (may be benign DROP/ALTER on fresh DB) ---"
        fi

        if [ "$RESTORE_RC" -gt 1 ]; then
          echo "pg_restore failed with exit code $RESTORE_RC" >&2
          exit "$RESTORE_RC"
        fi
        rm -f "$DUMP_FILE" "$RESTORE_LOG"

        # Verify that data was actually restored — show row counts.
        echo "Table row counts:"
        psql "$PREVIEW_DB_URL" -t -c "
          SELECT tablename, n_live_tup
          FROM pg_stat_user_tables
          WHERE schemaname = 'public'
            AND n_live_tup > 0
          ORDER BY n_live_tup DESC
          LIMIT 30;
        "
        TABLE_COUNT="$(psql "$PREVIEW_DB_URL" -t -c \
          "SELECT count(*) FROM pg_tables WHERE schemaname='public'")"
        if [ "$${TABLE_COUNT:-0}" -eq 0 ]; then
          echo "WARNING: seed produced an empty database" >&2
        else
          echo "Seed complete: $TABLE_COUNT tables restored"
        fi
      else
        echo "WARNING: pg_dump from sample DB failed — preview will start without seeded data" >&2
        rm -f "$DUMP_FILE"
      fi

      # Run Django management commands against the freshly seeded database.
      # Uses the Docker image that was just built; only runs when the seed
      # runs (clear_db=true or SAMPLE_DB_URI changed).
      echo "Running Django management commands..."
      IMAGE="rg.fr-par.scw.cloud/ns-qfdmo/webapp:$${IMAGE_TAG}"
      docker pull "$IMAGE"
      docker run --rm \
        -e DATABASE_URL="$PREVIEW_DB_URL" \
        -e SECRET_KEY=dummy \
        "$IMAGE" \
        sh -c "
          set -e
          python manage.py createcachetable
          python manage.py migrate
          python manage.py enable_unaccent
          python manage.py enable_trigram || true
          python manage.py purge_orphan_searchterm_index || true
          echo 'Management commands complete.'
        "
    EOT
  }

  triggers = {
    image_tag      = var.clear_db ? var.image_tag : "reuse"
    sample_db_hash = md5(var.sample_db_uri)
    seed_version   = "3" # bump to force re-seed (e.g. when changing restore logic)
  }
}
