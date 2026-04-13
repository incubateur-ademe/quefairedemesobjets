FROM nginx:alpine
RUN apk add --no-cache ruby
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/entrypoint.sh /entrypoint.sh
COPY servers.conf.erb /etc/nginx/servers.conf.erb
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
