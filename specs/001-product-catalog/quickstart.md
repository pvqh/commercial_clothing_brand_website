# Quickstart: Product Catalog

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

How to run the catalog locally and prove each user story works. Commands are for the repository
root. Implementation details live in `tasks.md` and the code, not here.

## Prerequisites

| Tool | Version | Why |
|------|---------|-----|
| [uv](https://docs.astral.sh/uv/) | latest | Installs Python 3.13 and all dependencies |
| Docker Desktop | latest | Local PostgreSQL 17 |
| Node.js | 22 LTS | Only for Lighthouse CI and stylelint |
| Git | any | |

## Setup

```powershell
uv sync                                   # Python 3.13 + dependencies from uv.lock
uv run playwright install chromium        # browser for end-to-end and accessibility tests
Copy-Item .env.example .env               # then set SECRET_KEY; DATABASE_URL defaults to Docker
docker compose -f deploy/compose.dev.yml up -d db
uv run python manage.py migrate
uv run python manage.py createsuperuser   # the admin account (password ≥ 12 characters)
```

## Load sample data and run

```powershell
uv run python -m tests.fixtures.build_sample_catalog         # writes the sample workbook and its photos
uv run python manage.py import_catalog tests/fixtures/sample_catalog.xlsx --photos tests/fixtures/photos --run-by <admin> --dry-run
uv run python manage.py import_catalog tests/fixtures/sample_catalog.xlsx --photos tests/fixtures/photos --run-by <admin>
uv run python manage.py runserver
```

Open <http://localhost:8000/> (Russian), <http://localhost:8000/en/> (English) and
<http://localhost:8000/staff/> (staff area).

The sample workbook deliberately contains invalid rows. The dry run and the real run must both
list them with sheet, row and reason (see [contracts/catalog-import.md](./contracts/catalog-import.md)).

## Validation scenarios

Each scenario is also an automated end-to-end test (`tests/e2e/`). Run them manually the first
time to see the behaviour.

| # | Story | Steps | Expected |
|---|-------|-------|----------|
| 1 | US1 | Open a category from the navigation; go to page 2; open a product | 24 cards per page, newest first; page 2 has its own address; product page shows photos, texts, fur details and price |
| 2 | US1 | Unpublish a product in the staff area, then open its address | 404 page with a link back to the catalog |
| 3 | US2 | On the sample coat with 3 colors × 5 sizes, select each color | Gallery and size availability change; zero-stock sizes are visible, disabled and labelled "Out of stock" |
| 4 | US2 | Open the sample product whose variants all have zero stock | Page loads (200) with "Sold out"; its listing card shows "Sold out" |
| 5 | US3 | In a category, filter by sizes M + L and a price range, then sort by price ascending | Only matching in-stock products, ordered by lowest matching price; result count updates; address contains the filters |
| 6 | US3 | Copy the filtered address into a private window | Same results and order (SC-004) |
| 7 | US3 | Open `?price_min=200000&price_max=100000&size=zz&page=99` | 302 to an address with the prices swapped, `size` dropped and the last valid page |
| 8 | US3 | Turn JavaScript off in the browser and repeat scenario 5 | Same results via the Apply button |
| 9 | US4 | Open the size guide on a coat, close it with Escape | Measurements in cm and inches; focus returns to the button; selections kept. A one-size scarf shows no selector or guide |
| 10 | US5 | Compare the sample catalog with the workbook | Every valid category, product, variant, photo and guide present; invalid products saved as drafts and listed in `sample_catalog-report.csv` |
| 11 | US5 | Run the import again | Refused: a completed import already exists |
| 12 | US6 | As the admin, create a staff account; sign in as staff; change a price, stock, publish status, a description and delete a photo | Each change visible on the shop within 60 s; each listed in Change history with name, time, old → new |
| 13 | US6 | Undo the price change; then try undoing an older change to a field that changed again | First: old price restored and the undo recorded. Second: refused with a reason |
| 14 | US6 | Enter a wrong password 5 times, then the right one | Locked for 15 minutes |
| 15 | US6 | Disable the staff account, then sign in with it | Refused; its earlier changes still show its name |
| 16 | US6 | Check the Products list "Missing English" filter | Products without English text are flagged |
| 17 | Lang | On any product, switch to English and back | Same product at its English address (`/en/product/<slug>/`) and back; missing English text shows the Russian text |
| 18 | SEO | View source of a product page | Title, description, canonical, hreflang, Open Graph and valid `Product`/`Offer`/`BreadcrumbList` JSON-LD |
| 19 | Design | Open a listing and a product page at 360 px and 1440 px wide, next to [design-reference.md](./design-reference.md) §2 and §5 | Layout follows the component map (2:3 cards, filter bar with «Показать», info panel with accordions, dark footer); no colors, fonts or spacing outside `tokens.css` (stylelint passes); no reference assets in `static/` |

## Automated checks (the same gates CI runs)

```powershell
uv run ruff check . ; uv run ruff format --check .
uv run mypy .
npx stylelint "static/css/**/*.css"
uv run pytest tests/unit tests/integration       # needs the Docker database
uv run pytest tests/e2e tests/a11y               # starts a live server; Playwright + axe
npx @lhci/cli autorun                            # performance budgets (lighthouserc.json)
uv run pip-audit
gitleaks detect
```

All must pass. axe must report zero serious or critical violations. Lighthouse must meet the
budgets in [research.md](./research.md#r12-performance-budget-and-images-principle-i).

## Timing check for SC-008

```powershell
Measure-Command { uv run python manage.py import_catalog tests/fixtures/catalog_200_products.xlsx --photos tests/fixtures/photos_200 --run-by <admin> }
```

Run it against a fresh database. It must finish in under 15 minutes on the production VPS size.
