#!/bin/sh
# Generate one nginx server{} per ROUTE_<NAME>_{HOST,UPSTREAM} pair.
# Upstream is the Scaleway native hostname (no scheme); TLS is added here.
set -eu

CONF="${NGINX_ROUTES_CONF:-/etc/nginx/conf.d/routes.conf}"
TMP="$(mktemp)"

: > "$TMP"

route_lines="$(env | grep '^ROUTE_.*_HOST=' || true)"
if [ -n "$route_lines" ]; then
  echo "$route_lines" | sort | while IFS= read -r line; do
    var_name=${line%%=*}
    host=${line#*=}
    route=${var_name#ROUTE_}
    route=${route%_HOST}
    eval "upstream=\${ROUTE_${route}_UPSTREAM-}"

    if [ -z "$host" ] || [ -z "$upstream" ]; then
      echo "Skipping route ${route}: HOST or UPSTREAM empty" >&2
      continue
    fi

    cat >> "$TMP" <<EOF
server {
    listen 8080;
    server_name ${host};

    client_max_body_size 100m;

    location / {
        set \$upstream_host ${upstream};
        proxy_http_version 1.1;
        proxy_set_header Host \$upstream_host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \$connection_upgrade;
        proxy_ssl_server_name on;
        proxy_ssl_name \$upstream_host;
        proxy_pass https://\$upstream_host;
        proxy_connect_timeout 10s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        proxy_redirect off;
    }
}
EOF
  done
fi

mv "$TMP" "$CONF"
