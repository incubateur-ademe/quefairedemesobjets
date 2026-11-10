# Built from the repository root, for servers.conf.erb
FROM nginx:1.30-alpine

RUN apk add --no-cache ruby

COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/generate-routes.sh /docker-entrypoint.d/40-generate-routes.sh
COPY nginx/45-render-webapp.sh /docker-entrypoint.d/45-render-webapp.sh
COPY servers.conf.erb /etc/nginx/servers.conf.erb

RUN chmod +x /docker-entrypoint.d/40-generate-routes.sh \
      /docker-entrypoint.d/45-render-webapp.sh \
    && rm -f /etc/nginx/conf.d/default.conf \
    && touch /etc/nginx/conf.d/routes.conf

EXPOSE 8080
