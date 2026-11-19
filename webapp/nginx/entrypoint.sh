#!/bin/sh
set -e

# Without certificates (mkcert is optional), serve plain HTTP on $PORT
if [ ! -f "${SSL_CERT_PATH:-}" ]; then
  unset SSL_CERT_PATH SSL_CERT_KEY_PATH
fi

ruby -e "require 'erb'; puts ERB.new(File.read('/etc/nginx/servers.conf.erb')).result(binding)" \
  > /etc/nginx/servers.conf
exec nginx -g 'daemon off;'
