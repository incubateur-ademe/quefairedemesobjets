#!/bin/sh
# Render servers.conf.erb in every mode it serves, run `nginx -t` on each
# rendering in a container without network, and compare the Scalingo, local
# and preview renderings with the expected ones in scripts/nginx_check/.
#   NGINX_CHECK_UPDATE=1  rewrite the expected renderings after a wanted change
#   TEMPLATE              template to render (default: servers.conf.erb)
#   OUT_DIR               keep the renderings there (default: a temporary directory)
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXPECTED="$ROOT/scripts/nginx_check"
TEMPLATE="${TEMPLATE:-$ROOT/servers.conf.erb}"
NGINX_IMAGE="${NGINX_CHECK_IMAGE:-nginx:1.30-alpine}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
OUT_DIR="${OUT_DIR:-$WORK/out}"
mkdir -p "$OUT_DIR"

render() {
  mode="$1"
  shift
  # Only the mode's variables, plus what is needed to find ruby
  env -i PATH="$PATH" HOME="$HOME" "$@" ruby -e "require 'erb'; puts ERB.new(File.read(ARGV[0])).result(binding)" \
    "$TEMPLATE" > "$OUT_DIR/$mode.conf"
}

# Environment of each mode, as set by its platform
render scalingo-production PORT=5000 ENVIRONMENT=production \
  BASE_DOMAIN=quefairedemesdechets.ademe.fr
render scalingo-staging PORT=5000 ENVIRONMENT=staging \
  BASE_DOMAIN=quefairedemesdechets.incubateur.ademe.dev
# docker-compose.yml, lvao-proxy
render local PORT=80 NGINX_DISABLE_CACHE=0 \
  BASE_DOMAIN=quefairedemesdechets.ademe.local \
  UPSTREAM_HOST=host.docker.internal:8000 \
  SSL_CERT_PATH=/etc/nginx/ssl/cert.pem SSL_CERT_KEY_PATH=/etc/nginx/ssl/key.pem
# webapp/Dockerfile, stage 2
render preview NGINX_ALLOW_ALL_HOSTS=1 NGINX_DISABLE_CACHE=0 PORT=8000 \
  ENVIRONMENT=preview UPSTREAM_HOST=127.0.0.1:8001 BASE_DOMAIN=
# Defined but empty must behave as absent: compared with scalingo-production
render scalingo-production-empty PORT=5000 ENVIRONMENT=production \
  BASE_DOMAIN=quefairedemesdechets.ademe.fr \
  UPSTREAM_HOST= UPSTREAM_AUTH_TOKEN= NGINX_SERVER_NAMES= NGINX_PROXY_STATIC= \
  NGINX_GZIP= NGINX_ADMIN_MAX_BODY_SIZE= NGINX_CACHE_PATH= NGINX_CACHE_MAX_SIZE=
render gateway PORT=8080 ENVIRONMENT=production \
  BASE_DOMAIN=quefairedemesdechets.ademe.fr \
  NGINX_SERVER_NAMES="quefairedemesdechets.ademe.fr quefairedemesobjets.ademe.fr" \
  UPSTREAM_HOST=https://lvaoprodwebapp-webapp.functions.fnc.fr-par.scw.cloud \
  UPSTREAM_AUTH_TOKEN=00000000-0000-4000-8000-000000000000 \
  NGINX_PROXY_STATIC=1 NGINX_GZIP=1 NGINX_ADMIN_MAX_BODY_SIZE=100m \
  NGINX_CACHE_PATH=/var/cache/nginx/assistant NGINX_CACHE_MAX_SIZE=256m

mkdir -p "$WORK/ssl"
openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj /CN=localhost \
  -keyout "$WORK/ssl/key.pem" -out "$WORK/ssl/cert.pem" 2> /dev/null
# Without network, nginx -t can only resolve the local upstream from /etc/hosts
printf '127.0.0.1 localhost host.docker.internal\n' > "$WORK/hosts"
chmod -R a+r "$WORK"

status=0
for conf in "$OUT_DIR"/*.conf; do
  mode="$(basename "$conf" .conf)"
  # The gateway includes the rendering from its own nginx.conf
  if [ "$mode" = gateway ]; then
    mounts="-v $ROOT/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      -v $conf:/etc/nginx/conf.d/default.conf:ro"
  else
    mounts="-v $ROOT/webapp/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      -v $conf:/etc/nginx/servers.conf:ro"
  fi
  # shellcheck disable=SC2086 # mounts is split on purpose
  if docker run --rm --network none --entrypoint nginx $mounts \
    -v "$WORK/ssl:/etc/nginx/ssl:ro" \
    -v "$WORK/hosts:/etc/hosts:ro" \
    "$NGINX_IMAGE" -t -q; then
    echo "ok      $mode"
  else
    echo "FAILED  $mode"
    status=1
  fi
done

# Comments and blank lines left out. Only this machine's nameservers, found
# as the template finds them, are replaced: the resolver directive stays (the
# PostHog and IGN proxies fail without it) and any other address shows.
NAMESERVERS="$(awk '/^nameserver[[:space:]]+[0-9.]+$/ { printf "%s%s", sep, $2; sep = " " }' /etc/resolv.conf 2> /dev/null || true)"
NAMESERVERS="${NAMESERVERS:-8.8.8.8 8.8.4.4}"
export NAMESERVERS
normalize() {
  perl -ne 'next if /^\s*(#.*)?$/; s/^(\s*resolver) \Q$ENV{NAMESERVERS}\E (valid=)/$1 <nameservers> $2/; print' "$1"
}
for mode in scalingo-production scalingo-staging local preview gateway; do
  if [ "${NGINX_CHECK_UPDATE:-}" = 1 ]; then
    mkdir -p "$EXPECTED"
    normalize "$OUT_DIR/$mode.conf" > "$EXPECTED/$mode.conf"
    echo "updated $EXPECTED/$mode.conf"
  elif normalize "$OUT_DIR/$mode.conf" | diff -u "$EXPECTED/$mode.conf" -; then
    echo "ok      $mode matches scripts/nginx_check/$mode.conf"
  else
    echo "FAILED  $mode differs from scripts/nginx_check/$mode.conf" \
      "(NGINX_CHECK_UPDATE=1 make nginx-check if the change is wanted)"
    status=1
  fi
done
if normalize "$OUT_DIR/scalingo-production-empty.conf" |
  diff -u "$EXPECTED/scalingo-production.conf" -; then
  echo "ok      empty variables render as absent ones"
else
  echo "FAILED  an empty variable is not treated as absent"
  status=1
fi
exit $status
