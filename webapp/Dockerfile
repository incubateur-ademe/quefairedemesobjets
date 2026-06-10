############################################
# Stage 1: build frontend assets (Node)
############################################
FROM node:24-slim AS node_build

WORKDIR /app

# Install JS deps first for better caching
COPY package.json package-lock.json ./
RUN npm ci

# Parcel build inputs
COPY . ./
RUN npm run build


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
    && rm -rf /var/lib/apt/lists/*

# Install uv (official installer)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --no-modify-path

# Install python deps (cached as long as lockfiles unchanged)
COPY pyproject.toml uv.lock ./
RUN /root/.local/bin/uv sync --frozen --no-dev

# Use the venv for subsequent RUN/CMD
ENV VIRTUAL_ENV="/app/.venv" \
    PATH="/app/.venv/bin:${PATH}"

# Copy app code
COPY . ./

# Internationalisation and customisation of Wagtail messages.
# SECRET_KEY is the only env var without a default in settings; any value
# works for build-time management commands.
RUN SECRET_KEY=dummy python manage.py compilemessages -l fr

# Copy built frontend assets, then collect them
COPY --from=node_build /app/static/compiled ./static/compiled
RUN SECRET_KEY=dummy python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["./bin/entrypoint.sh"]
