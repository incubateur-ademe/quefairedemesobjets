FROM nginx:alpine
RUN apk add --no-cache ruby
COPY webapp/nginx/nginx.conf /etc/nginx/nginx.conf
COPY webapp/nginx/entrypoint.sh /entrypoint.sh
COPY servers.conf.erb /etc/nginx/servers.conf.erb
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
