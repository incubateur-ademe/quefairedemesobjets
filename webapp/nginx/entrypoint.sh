#!/bin/sh
set -e
ruby -e "require 'erb'; puts ERB.new(File.read('/etc/nginx/servers.conf.erb')).result(binding)" \
  > /etc/nginx/servers.conf
exec nginx -g 'daemon off;'
