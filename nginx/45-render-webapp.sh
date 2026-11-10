#!/bin/sh
# Serve the webapp from servers.conf.erb, the template Scalingo and the local
# proxy also render. Does nothing while WEBAPP_UPSTREAM is empty.
# The rendered file holds the IAM key: never print it, nor run `nginx -T`
# where its output is logged.
# -f: server names such as *.example.fr must not glob
set -euf

[ -n "${WEBAPP_UPSTREAM:-}" ] || exit 0

CONF=/etc/nginx/conf.d/webapp.conf
HOST_RE='[a-z0-9]([a-z0-9.-]*[a-z0-9])?'
UUID_RE='[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
NEWLINE='
'

fail() {
  echo "45-render-webapp.sh: $*" >&2
  exit 1
}

# The whole value matches the extended regex, on a single line
matches() {
  case "$1" in *"$NEWLINE"*) return 1 ;; esac
  printf '%s\n' "$1" | grep -Eqx "$2"
}

matches "$WEBAPP_UPSTREAM" "https://$HOST_RE/?" \
  || fail "WEBAPP_UPSTREAM must be https://<host>"
matches "${WEBAPP_BASE_DOMAIN:-}" "$HOST_RE" \
  || fail "WEBAPP_BASE_DOMAIN must be a host name"
matches "${WEBAPP_ENVIRONMENT:-}" '[a-z]+' \
  || fail "WEBAPP_ENVIRONMENT must be set (production, staging...)"
if [ -n "${WEBAPP_AUTH_TOKEN:-}" ]; then
  matches "$WEBAPP_AUTH_TOKEN" "$UUID_RE" \
    || fail "WEBAPP_AUTH_TOKEN is not a UUID"
fi
# Host names (*.<host> accepted), or a regex for the preview gateway
server_names="${WEBAPP_SERVER_NAMES:-$WEBAPP_BASE_DOMAIN}"
matches "$server_names" '[^;{}"#'"'"']+' \
  || fail "WEBAPP_SERVER_NAMES must not contain ; { } # or quotes"
for name in $server_names; do
  # A final backslash would escape the semicolon nginx's server_name ends with
  matches "$name" "((\*\.)?$HOST_RE|~.*[^\\])" \
    || fail "WEBAPP_SERVER_NAMES: not a host name nor a ~regex: $name"
done

umask 077
# env -i: the template sees none of the gateway's own variables
env -i \
  PORT=8080 \
  ENVIRONMENT="$WEBAPP_ENVIRONMENT" \
  BASE_DOMAIN="$WEBAPP_BASE_DOMAIN" \
  NGINX_SERVER_NAMES="$server_names" \
  UPSTREAM_HOST="$WEBAPP_UPSTREAM" \
  UPSTREAM_AUTH_TOKEN="${WEBAPP_AUTH_TOKEN:-}" \
  NGINX_PROXY_STATIC=1 \
  NGINX_GZIP=1 \
  NGINX_ADMIN_MAX_BODY_SIZE=100m \
  NGINX_CACHE_PATH=/var/cache/nginx/assistant \
  NGINX_CACHE_MAX_SIZE=256m \
  /usr/bin/ruby -e "require 'erb'; puts ERB.new(File.read(ARGV[0])).result(binding)" \
  /etc/nginx/servers.conf.erb > "$CONF.tmp"
mv "$CONF.tmp" "$CONF"
