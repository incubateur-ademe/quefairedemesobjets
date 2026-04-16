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
FROM python:3.12-slim-bookworm AS webapp_builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    # FIXME : test if we need it
    PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# System deps (Aptfile) + common runtime libs
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      # FIXME : document it is because of djangomodel or remove git
      git \
      gettext \
      gdal-bin \
      libgdal-dev \
      libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Install uv (official installer)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --no-modify-path

# Install python deps (cached as long as lockfiles unchanged)
COPY pyproject.toml uv.lock ./
#  FIXME : should we add --no-dev ?
RUN uv sync --frozen

# Ensure the venv is used for subsequent RUN/CMD
ENV VIRTUAL_ENV="/app/.venv" \
# FIXME : should we add /root/.local/bin ?
    PATH="/app/.venv/bin:/root/.local/bin:${PATH}"

# Copy app code
# FIXME : on peut être plus précis sur ce qu'on copie ?
# peut-être pas besoin de static
COPY . ./

# (Internationalisation et) Customisation des messages de Wagtail
RUN SECRET_KEY=dummy python manage.py compilemessages -l fr

# Copy built frontend assets
COPY --from=node_build /app/static/compiled ./static/compiled

RUN SECRET_KEY=dummy python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["./bin/entrypoint.sh"]

