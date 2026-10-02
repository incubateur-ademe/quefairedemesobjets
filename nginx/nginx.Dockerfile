FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/nginx.conf
COPY generate-routes.sh /docker-entrypoint.d/40-generate-routes.sh

RUN chmod +x /docker-entrypoint.d/40-generate-routes.sh \
    && rm -f /etc/nginx/conf.d/default.conf \
    && touch /etc/nginx/conf.d/routes.conf

EXPOSE 8080
