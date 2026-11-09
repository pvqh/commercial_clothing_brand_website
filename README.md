# Fur brand catalog

A bilingual (Russian / English) online catalog for a fur clothing brand. Shoppers browse
categories, filter by size and price, choose a color and size, and read the size guide. Staff keep
the catalog current in a staff area at `/staff/`, where every change is recorded and can be undone.
The launch catalog is loaded once from a spreadsheet.

Feature specification, plan and decisions: [`specs/001-product-catalog/`](specs/001-product-catalog/)
([plan](specs/001-product-catalog/plan.md), [research](specs/001-product-catalog/research.md),
[quickstart and validation scenarios](specs/001-product-catalog/quickstart.md)).

Before changing the code, read [`GLOSSARY.md`](GLOSSARY.md) for the domain words. Then read
[`docs/architecture-review.md`](docs/architecture-review.md), which covers the clean-up backlog,
the planned refactors, and where new code goes.

## Stack

| Part | Technology |
|------|------------|
| Web framework | Python 3.13, Django 6.1 (server-rendered templates) |
| Database | PostgreSQL 17 (managed, hosted in Russia) |
| Interactivity | HTMX 2 on top of pages that work without JavaScript |
| Styling | Plain CSS with design tokens in `static/css/tokens.css` |
| Photos | Pillow renditions: AVIF, WebP and JPEG at 360–1440 px |
| Staff area | Customised Django admin with an append-only change history |
| Sign-in protection | django-axes (lockout), 12-character passwords, 2-hour sessions |
| Serving | Gunicorn + WhiteNoise behind Caddy (HTTPS), Docker Compose |
| Tests | pytest, pytest-django, Playwright, axe-core, Lighthouse CI |

## Run it locally (Windows PowerShell)

```powershell
uv sync                                         # Python 3.13 and dependencies
uv run playwright install chromium              # browser for the browser tests
Copy-Item .env.example .env                     # then set SECRET_KEY
docker compose -f deploy/compose.dev.yml up -d db
uv run python manage.py migrate
uv run python manage.py compilemessages         # needs GNU gettext
uv run python manage.py seed_demo_catalog       # demo data: 2 categories, 30 products
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

If another PostgreSQL already uses port 5432, start Docker with `$env:CATALOG_DB_PORT=5433` and use
port 5433 in `DATABASE_URL`.

Open <http://localhost:8000/> (Russian), <http://localhost:8000/en/> (English) and
<http://localhost:8000/staff/> (staff area).

## Tests

```powershell
uv run pytest tests/unit tests/integration tests/seo     # fast checks
uv run pytest tests/e2e tests/a11y                       # browser and accessibility checks
uv run pytest tests/integration/test_import_timing.py -m slow   # 200-product import (SC-008)
uv run ruff check . ; uv run ruff format --check . ; npm run lint:css
```

## Loading the launch catalog

Staff fill in `catalog_import/catalog_template.xlsx` following
[`catalog_import/WORKBOOK_FORMAT.md`](catalog_import/WORKBOOK_FORMAT.md) (in Russian). The admin then
runs `import_catalog` with `--dry-run` first; see the quickstart.

## Deployment

`deploy/compose.yml` runs the web app and Caddy; `deploy/.env.example` lists the settings.
`deploy/systemd/` holds the daily privacy-maintenance timer.
