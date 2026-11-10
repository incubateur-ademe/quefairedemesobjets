#!/bin/sh
# Offline test of the gateway serving the webapp: a fake Scaleway edge (nginx
# with TLS) answers for the webapp, PostHog, IGN and an Airflow route on an
# --internal network. Names are unique to the run, so runs can overlap.
set -eu

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RUN="$$-$(date +%s)"
P="qfdmo-gwt-$RUN"
IMAGE="qfdmo-gateway-test:$RUN"
NET="$P"
NATIVE=lvaotestwebapp-webapp.functions.fnc.fr-par.scw.cloud
OTHER=lvaotestother-webapp.functions.fnc.fr-par.scw.cloud
TOKEN=11111111-2222-4333-8444-555555555555
TRIES=150 # 30 s
WORK="$(mktemp -d)"
containers=""
network=""
image=""

# shellcheck disable=SC2329 # called by the trap
cleanup() {
  # shellcheck disable=SC2086 # one argument per container
  [ -z "$containers" ] || docker rm -f $containers > /dev/null 2>&1 || true
  [ -z "$network" ] || docker network rm "$NET" > /dev/null 2>&1 || true
  [ -z "$image" ] || docker rmi "$IMAGE" > /dev/null 2>&1 || true
  rm -rf "$WORK"
}
trap cleanup EXIT

fail=0
check() { # description, expected substring, actual
  case "$3" in
    *"$2"*) echo "ok      $1" ;;
    *) echo "FAILED  $1: expected '$2' in '$3'"; fail=1 ;;
  esac
}

cd "$WORK"
# One CA the gateway trusts, one it does not
for ca in trusted other; do
  openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj "/CN=$ca CA" \
    -keyout "$ca-ca.key" -out "$ca-ca.pem" 2> /dev/null
done
cert() { # name, ca, SANs
  openssl req -newkey rsa:2048 -nodes -subj "/CN=$1" -keyout "$1.key" \
    -out "$1.csr" 2> /dev/null
  printf 'subjectAltName=%s\n' "$3" > "$1.ext"
  openssl x509 -req -in "$1.csr" -CA "$2-ca.pem" -CAkey "$2-ca.key" \
    -CAcreateserial -days 1 -extfile "$1.ext" -out "$1.pem" 2> /dev/null
}
cert edge trusted "DNS:$NATIVE,DNS:eu.i.posthog.com,DNS:data.geopf.fr"
cert other other "DNS:$OTHER"
mkdir srv
# HTML above gzip_min_length, sent uncompressed by the edge
awk 'BEGIN { printf "<html><body>"; for (i = 0; i < 200; i++) printf "<p>page</p>"; print "</body></html>" }' \
  > srv/page.html
cat > edge.conf << 'EOF'
server {
    listen 443 ssl;
    ssl_certificate /certs/cert.pem;
    ssl_certificate_key /certs/key.pem;
    root /srv;
    location = /page.html {
    }
    location = /static/missing.css {
        add_header Cache-Control "public, max-age=600" always;
        return 404;
    }
    location / {
        return 200 "host=$host sni=$ssl_server_name xfh=$http_x_forwarded_host token=[$http_x_auth_token]\n";
    }
}
EOF
chmod -R a+r .

image=1
docker build -q -t "$IMAGE" -f "$ROOT/nginx/nginx.Dockerfile" "$ROOT" > /dev/null
network=1
docker network create --internal "$NET" > /dev/null
run() { # container, docker run arguments
  name="$P-$1"
  shift
  containers="$containers $name"
  docker run -d --name "$name" --network "$NET" "$@" > /dev/null
}
edge() { # container, cert, alias...
  c="$1" crt="$2"
  shift 2
  aliases=""
  for a in "$@"; do aliases="$aliases --network-alias $a"; done
  # shellcheck disable=SC2086 # one --network-alias per alias
  run "$c" $aliases -v "$WORK/edge.conf:/etc/nginx/conf.d/default.conf:ro" \
    -v "$WORK/srv:/srv:ro" \
    -v "$WORK/$crt.pem:/certs/cert.pem:ro" -v "$WORK/$crt.key:/certs/key.pem:ro" \
    nginx:1.30-alpine
}
edge edge edge "$NATIVE" eu.i.posthog.com data.geopf.fr
edge other other "$OTHER"
edge_ip="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$P-edge")"
gateway() { # container, upstream host, token, extra docker run arguments
  c="$1" upstream="$2" token="$3"
  shift 3
  run "$c" -v "$WORK/trusted-ca.pem:/etc/ssl/certs/ca-certificates.crt:ro" \
    -e WEBAPP_UPSTREAM="https://$upstream" -e WEBAPP_AUTH_TOKEN="$token" \
    -e WEBAPP_BASE_DOMAIN=site.test -e WEBAPP_SERVER_NAMES="site.test alias.test" \
    -e WEBAPP_ENVIRONMENT=staging "$@" "$IMAGE"
}
# The gateway's own variables below must not reach the template (env -i)
gateway gateway "$NATIVE" "$TOKEN" \
  -e ROUTE_AIRFLOW_HOST=airflow.test -e ROUTE_AIRFLOW_UPSTREAM="$edge_ip" \
  -e NGINX_ALLOW_ALL_HOSTS=1 -e NGINX_DISABLE_CACHE=1 -e ENVIRONMENT=prod
gateway badca "$OTHER" "$TOKEN"
gateway badkey "$NATIVE" "not-a-uuid"

wait_for() { # container, url
  i=0
  until docker exec "$P-$1" curl -sfk -o /dev/null "$2" 2> /dev/null; do
    i=$((i + 1))
    if [ "$(docker inspect -f '{{.State.Status}}' "$P-$1")" = exited ]; then
      echo "FAILED  $1 exited at startup"
      docker logs "$P-$1" 2>&1 | tail -5
      exit 1
    fi
    if [ $i -ge $TRIES ]; then
      echo "FAILED  $1 not ready after 30 s"
      docker logs "$P-$1" 2>&1 | tail -5
      exit 1
    fi
    sleep 0.2
  done
}
wait_exited() { # container
  i=0
  until [ "$(docker inspect -f '{{.State.Status}}' "$P-$1")" = exited ]; do
    i=$((i + 1))
    [ $i -lt $TRIES ] || return 0
    sleep 0.2
  done
}
wait_for edge https://127.0.0.1/
wait_for other https://127.0.0.1/
wait_for gateway http://127.0.0.1:8080/healthz
wait_for badca http://127.0.0.1:8080/healthz
wait_exited badkey

get() { # container, host, path, extra curl arguments
  c="$1" host="$2" path="$3"
  shift 3
  docker exec "$P-$c" curl -s "$@" -H "Host: $host" \
    -w ' status=%{http_code} cache=%header{x-cache-status} enc=%header{content-encoding} location=%header{location}' \
    "http://127.0.0.1:8080$path"
}
check "webapp: native Host, SNI, public X-Forwarded-Host, token" \
  "host=$NATIVE sni=$NATIVE xfh=site.test token=[$TOKEN]" "$(get gateway site.test /)"
check "env -i: NGINX_DISABLE_CACHE of the container ignored" "status=200 cache=HIT" \
  "$(get gateway site.test /)"
check "admin: token" "xfh=site.test token=[$TOKEN]" "$(get gateway site.test /admin/)"
get gateway site.test /static/app.css > /dev/null
check "static: cached" "status=200 cache=HIT" "$(get gateway site.test /static/app.css)"
get gateway site.test /static/missing.css > /dev/null
check "static: 404 not cached" "status=404 cache=MISS" \
  "$(get gateway site.test /static/missing.css)"
check "posthog: no token, even the client's" \
  "host=eu.i.posthog.com sni=eu.i.posthog.com xfh= token=[]" \
  "$(get gateway site.test /ph/e/ -H 'X-Auth-Token: from-client')"
check "ign: no token, even the client's" "host=data.geopf.fr sni=data.geopf.fr xfh= token=[]" \
  "$(get gateway site.test /tuiles/plan-ign/0/0/0.pbf -H 'X-Auth-Token: from-client')"
check "webapp: gzip" "enc=gzip location=" \
  "$(get gateway site.test /page.html -o /dev/null -H 'Accept-Encoding: gzip')"
check "airflow route: no gzip" "status=200 cache= enc= location=" \
  "$(get gateway airflow.test /page.html -o /dev/null -H 'Accept-Encoding: gzip')"
check "env -i: NGINX_ALLOW_ALL_HOSTS of the container ignored (alias redirected)" \
  "status=301 cache= enc= location=https://site.test/x" "$(get gateway alias.test /x)"
check "unknown host: default server" "status=404" "$(get gateway unknown.test /)"
check "healthz with an IP Host" "status=200" "$(get gateway 100.96.3.4:8080 /healthz)"
check "rendered config readable by root only" "-rw-------" \
  "$(docker exec "$P-gateway" ls -l /etc/nginx/conf.d/webapp.conf)"
check "certificate from another CA: 502" "status=502" "$(get badca site.test /)"
check "malformed key: container stopped" "exited 1" \
  "$(docker inspect -f '{{.State.Status}} {{.State.ExitCode}}' "$P-badkey")"
check "malformed key: reason logged" "WEBAPP_AUTH_TOKEN is not a UUID" \
  "$(docker logs "$P-badkey" 2>&1)"
logs="$(docker logs "$P-gateway" 2>&1)"
check "log_format: cache status and timings" "cache=HIT" "$logs"
check "log_format: upstream connect time" "uct=" "$logs"
case "$logs$(docker logs "$P-badkey" 2>&1)" in
  *"$TOKEN"* | *not-a-uuid*) echo "FAILED  logs contain the key"; fail=1 ;;
  *) echo "ok      logs never contain the key" ;;
esac
exit $fail
