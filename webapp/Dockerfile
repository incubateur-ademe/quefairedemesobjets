############################################
# Stage 1: build frontend assets (Node)
############################################
FROM node:24-slim AS node_build

WORKDIR /build

# Install JS deps first for better caching
COPY package-lock.json package.json .
COPY webapp/package.json webapp/package.json
COPY webapp/revue-front/package.json webapp/revue-front/package.json
RUN npm ci -w webapp -w webapp/revue-front
COPY webapp/ ./webapp/
RUN npm -w webapp run build
RUN npm -w webapp/revue-front run build


############################################
# Stage 2: render nginx ERB config (Ruby)
############################################
# Compiles servers.conf.erb — the same template Scalingo uses — with
# preview-appropriate values baked in at build time.
FROM ruby:alpine AS nginx_config

WORKDIR /build
COPY servers.conf.erb .

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
# Stage 3: system packages needed at runtime
############################################
FROM python:3.12-slim-bookworm AS runtime_base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV="/app/.venv" \
    PATH="/app/.venv/bin:${PATH}"

# GDAL for GeoDjango, libpq5 for psycopg (mirrors the Scalingo Aptfile)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      ca-certificates \
      gdal-bin \
      libpq5 \
      nginx \
    && rm -rf /var/lib/apt/lists/*


############################################
# Stage 4: Python dependencies and static files
############################################
FROM runtime_base AS python_build

ENV UV_LINK_MODE=copy \
    UV_NO_CACHE=1

# gettext for compilemessages, git for uv to install django-dsfr from its git
# fork (tool.uv.sources)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gettext git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /bin/

WORKDIR /app

# Install python deps (cached as long as lockfiles unchanged)
COPY pyproject.toml uv.lock .
COPY webapp/pyproject.toml webapp/pyproject.toml
RUN uv sync --project webapp --frozen --no-dev

# Copy app code
COPY webapp/ /app/webapp

# Internationalisation and customisation of Wagtail messages.
# This must be ran from git repo root for some obscure reason.
# Running it from webapp subdirectory causes issues
RUN SECRET_KEY=dummy python /app/webapp/manage.py compilemessages -l fr

WORKDIR /app/webapp
# Copy built frontend assets, then collect them
COPY --from=node_build /build/webapp/static/compiled/ static/compiled/
RUN SECRET_KEY=dummy python manage.py collectstatic --noinput


############################################
# Stage 5: runtime
############################################
FROM runtime_base

# Kept apart, so a code change does not push all the dependencies again
COPY --from=python_build /app/.venv /app/.venv
COPY --from=python_build /app/webapp /app/webapp
# Run by CI before a preprod/prod rollout, as Scalingo's postdeploy does
COPY bin/post_deploy /app/bin/post_deploy

WORKDIR /app/webapp

# Nginx: use the same nginx.conf + rendered servers.conf as Scalingo.
# The rendered servers.conf is compiled in stage 2 with preview vars.
RUN rm -f /etc/nginx/sites-enabled/default \
    && rm -f /etc/nginx/conf.d/default.conf 2>/dev/null
RUN mv nginx/nginx.conf /etc/nginx/nginx.conf
COPY --from=nginx_config /build/servers.conf /etc/nginx/servers.conf

EXPOSE 8000

CMD ["./bin/entrypoint.sh"]
