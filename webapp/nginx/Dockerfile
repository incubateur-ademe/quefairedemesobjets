# This is ran from the repo's root
# in the docker compose so paths reflect this behaviour.
# This is required because we share the servers.conf.erb that must be at the repo's
# root per Scalingo's requirements.
FROM nginx:alpine
RUN apk add --no-cache ruby
COPY webapp/nginx/nginx.conf /etc/nginx/nginx.conf
COPY webapp/nginx/entrypoint.sh /entrypoint.sh
COPY servers.conf.erb /etc/nginx/servers.conf.erb
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
