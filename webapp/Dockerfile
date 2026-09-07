############################################
# Stage 1: build frontend assets (Node)
############################################
FROM node:24-slim AS node_build

WORKDIR /build

# Install JS deps first for better caching
COPY webapp/ ./webapp/
COPY package-lock.json package.json .
RUN npm -w webapp ci
RUN npm -w webapp run build


############################################
# Stage 2: runtime (Python 3.12)
############################################
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# System deps: GDAL for GeoDjango, gettext for compilemessages,
# libpq5 for psycopg at runtime (mirrors the Scalingo Aptfile),
# git for uv to install django-dsfr from its git fork (tool.uv.sources),
# ruby (stdlib erb only) to render servers.conf.erb at container start, so
# one image serves every environment and ENVIRONMENT / BASE_DOMAIN come
# from the container env rather than being baked in at build time.
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
      ruby \
    && rm -rf /var/lib/apt/lists/*

# Install uv (official installer)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --no-modify-path

# Install python deps (cached as long as lockfiles unchanged)
COPY pyproject.toml uv.lock .
COPY webapp/pyproject.toml webapp/pyproject.toml
RUN /root/.local/bin/uv sync --project webapp --frozen --no-dev

# Use the venv for subsequent RUN/CMD
ENV VIRTUAL_ENV="/app/.venv" \
    PATH="/app/.venv/bin:${PATH}"

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

# Nginx: same nginx.conf and servers.conf.erb as Scalingo and the local
# lvao-proxy image. servers.conf is rendered by bin/entrypoint.sh at start.
RUN rm -f /etc/nginx/sites-enabled/default \
    && rm -f /etc/nginx/conf.d/default.conf 2>/dev/null
RUN mv nginx/nginx.conf /etc/nginx/nginx.conf
COPY servers.conf.erb /etc/nginx/servers.conf.erb

EXPOSE 8000

CMD ["./bin/entrypoint.sh"]
