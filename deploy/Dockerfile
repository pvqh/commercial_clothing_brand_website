# Web image: Django served by Gunicorn. Build from the repository root:
#   docker build -f deploy/Dockerfile -t fur-catalog-web .
FROM python:3.13-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /usr/local/bin/uv
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"
WORKDIR /app

FROM base AS build
RUN apt-get update && apt-get install -y --no-install-recommends gettext \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY . .
# Build-time values only; the real ones come from the environment at run time.
RUN SECRET_KEY=build-only DATABASE_URL=postgres://build@localhost/build \
    DJANGO_SETTINGS_MODULE=config.settings.prod \
    sh -c "python manage.py compilemessages && python manage.py collectstatic --noinput"

FROM base AS runtime
RUN useradd --create-home --uid 1000 catalog
COPY --from=build /opt/venv /opt/venv
COPY --from=build --chown=catalog:catalog /app /app
USER catalog
ENV DJANGO_SETTINGS_MODULE=config.settings.prod
EXPOSE 8000
CMD ["gunicorn", "config.wsgi", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60"]
