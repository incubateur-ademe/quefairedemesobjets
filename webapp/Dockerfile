############################################
# Stage 1: build frontend assets (Node)
############################################
FROM node:24-slim AS node_build

WORKDIR /build

# Install JS deps first for better caching
COPY webapp/ .
RUN npm ci
RUN npm run build


############################################
# Stage 2: render nginx ERB config (Ruby)
############################################
# Compiles servers.conf.erb — the same template Scalingo uses — with
# preview-appropriate values baked in at build time.
FROM ruby:alpine AS nginx_config

WORKDIR /build
COPY webapp/servers.conf.erb .

# PORT=8000: Scaleway container port (TLS terminated by Scaleway).
# NGINX_ALLOW_ALL_HOSTS=1: preview domain unknown at build time.
# UPSTREAM_HOST=127.0.0.1:8001: gunicorn on localhost, not a unix socket.
# NGINX_DISABLE_CACHE=0: keep caching for production fidelity.
RUN NGINX_ALLOW_ALL_HOSTS=1 \
    NGINX_DISABLE_CACHE=0 \
    PORT=8000 \
    ENVIRONMENT=preview \
    UPSTREAM_HOST=127.0.0.1:8001 \
    BASE_DOMAIN="" \
    ruby -e "require 'erb'; puts ERB.new(File.read('servers.conf.erb')).result(binding)" \
    > servers.conf


############################################
# Stage 3: runtime (Python 3.12)
############################################
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /opt/app

# System deps: GDAL for GeoDjango, gettext for compilemessages,
# libpq5 for psycopg at runtime (mirrors the Scalingo Aptfile),
# git for uv to install django-dsfr from its git fork (tool.uv.sources)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      gettext \
      gdal-bin \
      git \
      libgdal-dev \
      libpq5 \
      nginx \
    && rm -rf /var/lib/apt/lists/*

# Install uv (official installer)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --no-modify-path

# Install python deps (cached as long as lockfiles unchanged)
COPY pyproject.toml uv.lock .
COPY webapp/pyproject.toml webapp/pyproject.toml
RUN /root/.local/bin/uv sync --project webapp --frozen --no-dev

# Use the venv for subsequent RUN/CMD
ENV VIRTUAL_ENV="/opt/app/.venv" \
    PATH="/opt/app/.venv/bin:${PATH}"

# Copy app code
WORKDIR /opt/app/webapp
COPY webapp/ ./

# Internationalisation and customisation of Wagtail messages.
# SECRET_KEY is the only env var without a default in settings; any value
# works for build-time management commands.
# RUN DJANGO_SETTINGS_MODULE=settings.base SECRET_KEY=dummy python manage.py compilemessages -l fr

# Copy built frontend assets, then collect them
COPY --from=node_build /build/static/compiled/ static/compiled/

RUN DJANGO_SETTINGS_MODULE=settings.base SECRET_KEY=dummy python manage.py collectstatic --noinput

# Required while we share scalingo and scaleway config.
RUN mkdir -p /app/staticfiles
RUN cp -r /opt/app/webapp/staticfiles/* /app/staticfiles/

# Nginx: use the same nginx.conf + rendered servers.conf as Scalingo.
# The rendered servers.conf is compiled in stage 2 with preview vars.
RUN rm -f /etc/nginx/sites-enabled/default \
    && rm -f /etc/nginx/conf.d/default.conf 2>/dev/null
RUN mv nginx/nginx.conf /etc/nginx/nginx.conf
COPY --from=nginx_config /build/servers.conf /etc/nginx/servers.conf

EXPOSE 8000

CMD ["./bin/entrypoint.sh"]
