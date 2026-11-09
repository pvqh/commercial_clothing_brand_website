---

description: "Task list for the Product Catalog feature"
---

# Tasks: Product Catalog

**Input**: Design documents from `/specs/001-product-catalog/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md),
[design-reference.md](./design-reference.md)

**Tests**: Included. The constitution's quality gates require automated tests, accessibility checks,
SEO validation and performance budgets in CI before merge (research R16). Within each story, write
the tests first and confirm they fail before implementing.

**Out of scope (deferred by the brand, 2026-11-09)**: Russian numeric sizes, a fur-type filter, a
product article number, and the final accent color and logo (design-reference §7). Keep the letter
size scale, placeholder accent `#7A4B2A` and text-wordmark placeholder.

**Organization**: Tasks are grouped by user story. Phases follow spec priority: P1 stories (US1,
US2, US5, US6), then P2 (US3), then P3 (US4).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US6)
- Paths are relative to the repository root (single Django project, see plan.md "Project Structure")

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and tooling

- [X] T001 Create the uv project in `pyproject.toml` (Python 3.13; dependencies: Django 6.1, psycopg[binary] 3, dj-database-url, Pillow (AVIF support), openpyxl, django-axes 9, whitenoise, gunicorn; dev group: pytest, pytest-django, playwright, axe-playwright-python, ruff, mypy, django-stubs, pip-audit, pre-commit) and generate `uv.lock` with `uv lock`
- [X] T002 Create the Django project skeleton: `manage.py`, `config/__init__.py`, `config/wsgi.py`, `config/urls.py` (empty patterns), and empty app packages `catalog/`, `audit/`, `catalog_import/`, `field_metrics/` (each with `__init__.py` and `apps.py`)
- [X] T003 Create split settings in `config/settings/base.py`, `config/settings/dev.py`, `config/settings/test.py`, `config/settings/prod.py`: read `SECRET_KEY` and `DATABASE_URL` from the environment (dj-database-url), `LANGUAGE_CODE = "ru"`, `LANGUAGES = [("ru", "Русский"), ("en", "English")]`, `TIME_ZONE = "Europe/Moscow"`, `USE_I18N = True`, `LOCALE_PATHS = [BASE_DIR / "locale"]`, `TEMPLATES` dir `templates/`, `STATICFILES_DIRS = [BASE_DIR / "static"]`, `MEDIA_ROOT = BASE_DIR / "media"`, WhiteNoise compressed manifest storage, and the four apps installed
- [X] T004 [P] Create `deploy/compose.dev.yml` with a `db` service on image `postgres:17` (volume, port 5432) and `.env.example` with `SECRET_KEY`, `DATABASE_URL=postgres://catalog:catalog@localhost:5432/catalog` and `DJANGO_SETTINGS_MODULE=config.settings.dev`
- [X] T005 [P] Configure ruff (lint + format, line length 100), mypy with the django-stubs plugin, and pytest (`DJANGO_SETTINGS_MODULE = "config.settings.test"`, test paths `tests/`) in `pyproject.toml`
- [X] T006 [P] Create `package.json` (devDependencies only: stylelint, stylelint-config-standard, stylelint-declaration-strict-value, @lhci/cli) and `.stylelintrc.json` that rejects raw color, font-family and px spacing values in every `static/css/*.css` file except `static/css/tokens.css` (research R4)
- [X] T007 [P] Create `.pre-commit-config.yaml` running ruff, ruff-format, stylelint and gitleaks
- [X] T008 [P] Add Python, Django and Node entries to `.gitignore` (`.env`, `.venv/`, `__pycache__/`, `media/`, `staticfiles/`, `node_modules/`) while keeping the existing entries
- [X] T009 [P] Create the test layout: `tests/__init__.py`, `tests/conftest.py`, and empty packages `tests/unit/`, `tests/integration/`, `tests/e2e/`, `tests/a11y/`, `tests/seo/`, `tests/fixtures/`
- [X] T010 [P] Create `.github/workflows/ci.yml` with jobs `lint` (ruff, ruff format --check, mypy, stylelint), `test` (PostgreSQL 17 service; `pytest tests/unit tests/integration tests/seo`), `browser` (Playwright Chromium; `pytest tests/e2e tests/a11y`), and `security` (pip-audit, `npm audit --omit=dev`, gitleaks); every job required for merge

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Catalog data model, translations, URL scheme, design tokens, base layout and test
harness that every story uses

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Internationalisation and URLs

- [X] T011 Configure `config/urls.py` with `i18n_patterns(..., prefix_default_language=False)` so Russian is served at `/` and English under `/en/`; add `django.middleware.locale.LocaleMiddleware` to `config/settings/base.py`; do not include Django's `set_language` view and do not set any language cookie (research R6, FR-034)
- [X] T012 [P] Create the message catalogues `locale/ru/LC_MESSAGES/django.po` and `locale/en/LC_MESSAGES/django.po` (msgids in English; Russian translations in the `ru` file), including the URL path words `catalog/` → `katalog/` and `product/` → `tovar/`

### Catalog data model (data-model.md)

- [X] T013 [P] Create `catalog/models/choices.py`: `Size` as `IntegerChoices` with values 10 `xxs` XXS, 20 `xs` XS, 30 `s` S, 40 `m` M, 50 `l` L, 60 `xl` XL, 70 `xxl` XXL, 80 `xxxl` XXXL, 100 `one` "One size / Единый размер" ("Its numeric value **is** the display order"), with helpers `Size.from_code(code)` and `size.code`; and `FurTreatment` as `TextChoices` `natural`, `dyed`, `treated` with translated labels
- [X] T014 [P] Create `catalog/models/translated.py` with an abstract mixin providing `localized(field_name)`: returns `<field>_en` when the active language is English and the value is not blank, otherwise `<field>_ru` (FR-036); plus a template filter `localized` in `catalog/templatetags/catalog_tags.py`
- [X] T015 [P] Write `tests/unit/test_localized_fallback.py`: English value returned in English, Russian returned when English is blank, Russian always returned in Russian
- [X] T016 Create `catalog/models/category.py` `Category`: `name_ru` (text, ≤ 80, required), `name_en` (≤ 80, optional), `slug_ru` / `slug_en` ("slug, ≤ 100, each unique"), `position` ("small int ≥ 0"), `is_published` ("bool, default false"), timestamps; ordering by `position`
- [X] T017 Create `catalog/models/size_guide.py`: `SizeGuide` (`internal_name` "text, ≤ 100"; `how_to_measure_ru` required long text, `how_to_measure_en` optional); `SizeGuideRow` (`size_guide` FK cascade; `size` Size "excluding `one`", "Unique per guide"; `chest_cm`, `waist_cm`, `hips_cm`, `sleeve_cm`, `length_cm` as "decimal(5,1)", "> 0" via check constraints); `ProductType` (`name_ru` ≤ 80 required, `name_en` ≤ 80 optional, `size_guide` "FK SizeGuide, nullable, protect")
- [X] T018 Create `catalog/models/product.py` `Product` with every field in data-model.md: translated `name` (≤ 150), `description`, `care_instructions`, `fur_species` (≤ 100), `fur_origin_country` (≤ 100), `fur_treatment_detail` (≤ 200, "Required in Russian when `fur_treatment = treated`"), `shell_material` (≤ 200), `lining_material` (≤ 200), `trim_material` (≤ 200, "Optional"); `fur_treatment` (FurTreatment, required); `product_type` ("FK ProductType, protect"); `size_guide` ("FK SizeGuide, nullable, protect"); `slug_ru` / `slug_en` ("slug, ≤ 160, each unique"); `is_published` ("bool, default false"); `first_published_at` ("timestamp, nullable"; "Set once, the first time it is published; never reset"); Russian columns required, English columns blank-allowed; plus `ProductCategory` (`product` FK cascade, `category` FK protect, `position` small int ≥ 0, "`0` = primary", unique (product, category) and unique (product, position)); and derived properties `primary_category`, `effective_size_guide`, `is_one_size`, `is_sold_out`, `missing_english`
- [X] T019 Create `catalog/models/color_variant.py`: `Color` (`product` FK cascade; translated `name` ≤ 60, Russian required; `position` small int ≥ 0, "Unique per product; position 0 is the default selection"; derived `is_out_of_stock`); `Variant` (`color` FK cascade, "The product is `color.product` (no duplicate product column)"; `size` Size; `price_kopecks` "positive bigint", "> 0"; `stock` int "≥ 0 (database check constraint)"; "Unique (color, size)"; partial index on (`color_id`, `size`) "where `stock > 0`"; model validation "A product may not mix `one` with letter sizes")
- [X] T020 Create `catalog/models/photo.py` `ProductPhoto`: `product` FK cascade; `color` ("FK Color, nullable, set null"; empty = shared photo); `position` small int ≥ 0; `original` image file (JPEG/PNG/WebP); `width` / `height` positive int; translated `alt_text` ≤ 250 with "`alt_ru` required (FR-017)"; method `rendition_widths()` returning the widths in 360/720/1080/1440 that are ≤ `width`
- [X] T021 Create `catalog/models/slug_redirect.py` with an abstract base and concrete `CategorySlugRedirect` / `ProductSlugRedirect` (`category` or `product` FK cascade; `language` `ru`/`en`; `old_slug`, "Unique per (language, old_slug)"), and `catalog/models/__init__.py` exporting all models
- [X] T022 Generate `catalog/migrations/0001_initial.py` with `makemigrations`; add the indexes from research R13: `product(is_published, first_published_at)` and `productcategory(category_id, product_id)`

### Shared services

- [X] T023 [P] Write `tests/unit/test_slugs.py`: «Шуба из норки» → `shuba-iz-norki`, English name used for `slug_en` with fallback to `slug_ru`, a clash gets `-2`, a rename stores the previous slug as a redirect
- [X] T024 Implement `catalog/services/slugs.py`: Russian→Latin transliteration table, `slugify_ru(name)`, `assign_slugs(instance)` that regenerates `slug_ru`/`slug_en` from the names, makes them unique with a numeric suffix, and records each replaced slug in the matching `*SlugRedirect` table (research R7)
- [X] T025 [P] Write `tests/unit/test_photo_renditions.py`: a 1600 × 2400 source produces 360/720/1080/1440 in AVIF, WebP and JPEG at `photos/<id>/<width>.<format>`; a 900-wide source produces only 360 and 720; nothing is wider than the original
- [X] T026 Implement `catalog/services/photo_renditions.py`: `generate_renditions(photo)` using Pillow with the widths and paths above, a 2:3 crop check, and AVIF encoder speed tuned for throughput (research R12)
- [X] T027 Create `catalog/demo_catalog.py` with small builder functions (`build_category`, `build_product`, `build_color`, `build_variant`, `build_photo`, `build_size_guide`) that create valid records and generate grey 2:3 JPEG photos with the product name drawn on them (no third-party images), used by tests and the seed command
- [X] T028 Create `catalog/management/commands/seed_demo_catalog.py` that builds two published categories with 30 products, including one coat with 3 colors × 5 sizes and some zero-stock combinations, one fully sold-out product, one one-size scarf and one unpublished product

### Design system and layout (design-reference.md §5–6)

- [X] T029 [P] Create `static/css/tokens.css` with every token in design-reference.md §5 (colors, typography, spacing, radii, control heights, motion, `--ratio-product-photo: 2 / 3`), including the placeholder accent `#7A4B2A`
- [X] T030 [P] Add Manrope variable WOFF2 subset files `static/fonts/manrope-cyrillic.woff2` and `static/fonts/manrope-latin.woff2` (from Fontsource, SIL OFL) with `static/fonts/OFL.txt`
- [X] T031 Create `static/css/site.css` with `@layer reset, base, components, utilities`: reset, `@font-face` for both Manrope files (`font-display: swap`), base typography from tokens, `.container` (max `--container-max`, `--gutter`), visible focus ring (`--color-focus`, 2 px, offset 2 px), visually-hidden utility, `prefers-reduced-motion` rule, and mobile-first `min-width` breakpoints 600 / 1024 / 1440 px only
- [X] T032 [P] Create `static/icons/sprite.svg` with a Lucide subset (chevron-down, x, ruler, arrow-left, arrow-right, globe, menu) plus `static/icons/LICENSE` (ISC), and `templates/components/icon.html` rendering `<svg aria-hidden="true"><use href="…#name"></use></svg>`
- [X] T033 [P] Create `static/img/placeholder-2x3.svg` (grey `--color-surface-photo` box) and the text wordmark placeholder used by the header
- [X] T034 [P] Vendor HTMX 2.x as `static/vendor/htmx.min.js` with its licence file `static/vendor/htmx.LICENSE`
- [X] T035 Create `templates/base.html`: `<html lang>` from the active language, blocks for title, meta description, canonical, `hreflang` alternates, Open Graph and robots meta, JSON-LD; preload `manrope-cyrillic.woff2`; link `tokens.css` and `site.css`; `htmx.min.js` with `defer`; skip link; header, `<main id="main">`, footer
- [X] T036 [P] Create `catalog/context_processors.py` `navigation` returning published categories that have at least one published product, ordered by `position`, and register it in `config/settings/base.py`
- [X] T037 Create `templates/components/site_header.html` (wordmark placeholder, flat category links, a `<details>` menu below 1024 px, language switch) and `templates/components/language_switch.html` (link to `alternate_urls[other_language]` provided by the view, falling back to Django's `translate_url`) with their CSS sections in `static/css/site.css`
- [X] T038 [P] Create `templates/components/site_footer.html` (dark `--color-surface-inverse` footer with category links and the language switch) and its CSS section in `static/css/site.css`
- [X] T039 [P] Create `templates/components/button.html` (variants `primary`, `secondary` outlined pill, `icon` round; height `--control-height`) and its CSS section in `static/css/site.css`
- [X] T040 [P] Create `templates/components/picture.html` and a `picture` inclusion tag in `catalog/templatetags/catalog_tags.py`: `<picture>` with AVIF and WebP `<source>` and JPEG `<img>` `srcset` from `rendition_widths()`, `sizes` argument, explicit `width`/`height`, `alt` from `localized('alt_text')`, `loading="lazy"` unless `priority=True` (then `fetchpriority="high"`)
- [X] T041 [P] Write `tests/unit/test_price_format.py` and implement the `rubles` filter in `catalog/templatetags/catalog_tags.py`: kopecks → whole rubles with a narrow no-break space thousands separator and `₽` (`12500000` → `125 000 ₽`) in both languages (research R15)
- [X] T042 [P] Create `templates/components/price.html` (exact price, or «от» / "From" + lowest price) and `templates/components/breadcrumbs.html` (`<nav aria-label>` + `<ol>`) with CSS sections in `static/css/site.css`

### Test harness

- [X] T043 Create `tests/e2e/conftest.py`: Playwright Chromium fixtures on pytest-django's `live_server`, a `seeded_catalog` fixture using `catalog/demo_catalog.py`, and two browser contexts, `js_enabled` and `js_disabled`
- [X] T044 [P] Create `tests/a11y/conftest.py` with `assert_no_serious_axe_violations(page)` using axe-playwright-python, failing on any `serious` or `critical` violation (Principle II)

**Checkpoint**: Foundation ready. `uv run python manage.py migrate` and `seed_demo_catalog` work.
User story implementation can begin.

---

## Phase 3: User Story 1 - Browse a category and open a product (Priority: P1) 🎯 MVP

**Goal**: Shoppers open a category from the navigation, page through 24-product listings (newest
first) and open product pages with photos, texts, fur details and price, in Russian and English.

**Independent Test**: Seed two categories with published products; open each from the navigation;
confirm the right products appear newest first, 24 per page with page addresses, and each opens a
product page with photos, name, description and price; an unpublished product shows "not found".

### Tests for User Story 1 ⚠️

> Write these tests FIRST and confirm they FAIL before implementation.

- [X] T045 [P] [US1] Write `tests/integration/test_category_listing.py`: only published products listed; order `first_published_at DESC, id DESC`; 24 per page; `?page=2` serves page 2; `?page=1` and `?page=99` redirect 302 to the normalised address; unpublished category → 404; published category with no published products → 200 with `noindex`; category hidden from navigation when it has no published products; response has `Cache-Control: public, max-age=60` and no `Set-Cookie` header
- [X] T046 [P] [US1] Write `tests/integration/test_product_page.py`: a published product shows all its photos, name, description, fur species, origin country, treatment, shell/lining/trim, care instructions and price; breadcrumb and "back" link use the primary category even when opened from another category; unpublished product → 404 page containing a link to the catalog home
- [X] T047 [P] [US1] Write `tests/integration/test_language_urls.py`: `/katalog/<slug_ru>/` and `/en/catalog/<slug_en>/` serve the same category; the language switch links to the same page in the other language; English pages show Russian text where English is blank; an old slug answers 301 to the current slug in the same language
- [X] T048 [P] [US1] Write `tests/seo/test_us1_head_and_structured_data.py`: unique title and description, canonical (no query except `page` ≥ 2), `hreflang` ru/en/x-default, Open Graph tags on listing and product pages; product JSON-LD `Product` with `offers` (`Offer` or `AggregateOffer`, `priceCurrency` `RUB`) and `BreadcrumbList` home → primary category → product
- [X] T049 [P] [US1] Write `tests/e2e/test_us1_browse.py` (both `js_enabled` and `js_disabled`): open a category from the header, go to page 2, open a product, return via the breadcrumb
- [X] T050 [P] [US1] Write `tests/a11y/test_us1_pages.py`: axe on home, category listing, product page and the 404 page

### Implementation for User Story 1

- [X] T051 [US1] Implement `catalog/services/listing_query.py` `published_listing(category)`: published products in the category annotated with the lowest in-stock variant price, the lowest price of any variant, whether prices differ, and `is_sold_out`, ordered by `first_published_at DESC, id DESC`, with the listing photo prefetched (research R13; filters are added in US3)
- [X] T052 [US1] Implement `catalog/views/home.py`: catalog landing listing published navigation categories, `Cache-Control: public, max-age=60`
- [X] T053 [US1] Implement `catalog/views/category.py`: look up by `slug_<lang>` (404 when unknown or unpublished, 301 via `CategorySlugRedirect` for old slugs), paginate 24 per page, 302 to the normalised address for `page=1` or a page beyond the last, set `alternate_urls`, canonical, `noindex` when empty, `Cache-Control: public, max-age=60`
- [X] T054 [US1] Implement `catalog/views/product.py` (base version): look up by `slug_<lang>` (404 when unpublished, 301 via `ProductSlugRedirect`), gallery from shared photos ordered by `position`, "From" price, `alternate_urls`, canonical, `Cache-Control: public, max-age=60`
- [X] T055 [US1] Create `catalog/urls.py` with translated paths `""` (home), `_("catalog/") + "<slug:slug>/"`, `_("product/") + "<slug:slug>/"`, and include it in the `i18n_patterns` of `config/urls.py`
- [X] T056 [P] [US1] Create `templates/components/product_card.html` (2:3 `picture`, uppercase title via CSS with ellipsis on overflow, `price` component) and `templates/components/product_grid.html` (2 columns at 360 px, 3 from 600 px, 4 from 1024 px; `--grid-gap-*` tokens) with CSS sections in `static/css/site.css`
- [X] T057 [P] [US1] Create `templates/components/category_chips.html` (horizontal scroll-snap row of flat categories, `aria-current="page"` on the active one) and `templates/components/pagination.html` (numbered links with `rel="prev"`/`rel="next"`) with CSS sections in `static/css/site.css`
- [X] T058 [P] [US1] Create `templates/components/section_heading.html` (H1/H2 with an optional outlined pill link) with its CSS section in `static/css/site.css`
- [X] T059 [P] [US1] Create `templates/components/product_gallery.html`: horizontal scroll-snap strip below 1024 px and a two-column photo grid from 1024 px, first image `priority=True`, no carousel script; CSS section in `static/css/site.css`
- [X] T060 [P] [US1] Create `templates/components/info_accordion.html`: `<details>`/`<summary>` sections Characteristics (fur species, origin country, treatment and detail, shell, lining, trim; open by default), Description, Care; CSS section in `static/css/site.css`
- [X] T061 [US1] Create `templates/catalog/home.html`, `templates/catalog/category.html` (breadcrumbs, H1, category chips, result count in `aria-live="polite"`, grid, pagination) and `templates/catalog/product.html` (breadcrumbs, back link to the primary category, gallery, sticky info panel from 1024 px with H1 and price, accordions)
- [X] T062 [US1] Create `templates/404.html` ("not found" message and a link to the catalog home) and register `handler404` in `config/urls.py`
- [X] T063 [P] [US1] Implement `catalog/seo/structured_data.py`: `product_json_ld(product, request)` (`Product` with name, description, images, `sku` = product id, placeholder brand, `material`; `Offer` when one price else `AggregateOffer` with `lowPrice`/`highPrice`; `priceCurrency` `RUB`; availability; canonical `url`) and `breadcrumb_json_ld(...)`, rendered in `templates/catalog/product.html`
- [X] T064 [P] [US1] Implement `catalog/seo/sitemaps.py` (published categories and products in both languages with `hreflang` alternates) and a `robots.txt` view disallowing `/staff/` and linking `/sitemap.xml`; wire both in `config/urls.py` outside `i18n_patterns`
- [X] T065 [US1] Add every US1 interface string to `locale/ru/LC_MESSAGES/django.po` and `locale/en/LC_MESSAGES/django.po` and run `compilemessages`

**Checkpoint**: User Story 1 is fully functional and testable on its own (MVP).

---

## Phase 4: User Story 2 - Choose a size and color and see availability (Priority: P1)

**Goal**: On a product page, choosing a color shows that color's photos and size availability;
out-of-stock sizes and colors are labelled in text and cannot be chosen; sold-out products stay
live; prices show "From" until a variant is chosen.

**Independent Test**: Seed a coat with 3 colors × 5 sizes with some zero-stock combinations, and
confirm every combination's status on the product page matches the stock data.

### Tests for User Story 2 ⚠️

- [X] T066 [P] [US2] Write `tests/unit/test_product_availability.py`: per-color size availability, color out of stock when all its sizes have zero stock, product sold out when every variant has zero stock, price range and exact price per (color, size)
- [X] T067 [P] [US2] Write `tests/integration/test_product_variants.py`: `?color=<id>` switches the gallery to that color's photos (shared photos when the color has none); zero-stock sizes rendered with `disabled` and the text "Out of stock"/«Нет в наличии»; an all-zero color labelled out of stock; an invalid `color` → 302 without it; a sold-out product → 200 with "Sold out" and JSON-LD `OutOfStock`; its listing card shows "Sold out"; a single-color product shows no color selector; `color` views carry `noindex` and canonical to the product
- [X] T068 [P] [US2] Write `tests/e2e/test_us2_variants.py` (`js_enabled` and `js_disabled`): switch colors, see availability change, try to choose an out-of-stock size, choose an in-stock size and see the exact price
- [X] T069 [P] [US2] Write `tests/a11y/test_us2_variants.py`: axe on the 3-color coat page with a color selected and on the sold-out product page

### Implementation for User Story 2

- [X] T070 [US2] Implement `catalog/services/product_availability.py`: `availability_for(product, color)` returning sizes in scale order with stock and price for that color, `color_states(product)`, `price_range(product)` (research R13; data-model derived properties)
- [X] T071 [US2] Extend `catalog/views/product.py`: read and validate `color` (default: position 0), gallery for that color with shared-photo fallback, availability and price data in the context, `noindex` + canonical for `color` views, JSON-LD availability `InStock`/`OutOfStock`
- [X] T072 [P] [US2] Create `templates/components/color_options.html`: links `?color=<id>` with `aria-current="true"` on the selected color and a visible "Out of stock" text where applicable; hidden for single-color products; HTMX `hx-get`, `hx-select="#product-options"`, `hx-target="#product-options"`, `hx-push-url="true"`; CSS section in `static/css/site.css`
- [X] T073 [P] [US2] Create `templates/components/size_selector.html`: a radio group in `<fieldset>` with `<legend>`; chips 44 px tall; out-of-stock sizes `disabled`, crossed out **and** labelled "Out of stock" in text; when prices differ, each option's accessible name includes its price; hidden for one-size products (FR-029); CSS section in `static/css/site.css`
- [X] T074 [US2] Show the exact price for the chosen size without JavaScript: render one price element per in-stock size for the selected color plus the "From" element in `templates/catalog/product.html`, and add static `:has()` rules for the nine size codes in `static/css/site.css` so the checked size's price replaces "From" (FR-023)
- [X] T075 [US2] Wrap the gallery, color options, size selector and price in `#product-options` in `templates/catalog/product.html`, and show "Sold out" in the info panel when `is_sold_out` (FR-022)
- [X] T076 [US2] Add the "Sold out" label to `templates/components/product_card.html` and the "From" price when matching prices differ (FR-003, FR-023)
- [X] T077 [US2] Add every US2 interface string to both `locale/*/LC_MESSAGES/django.po` files and run `compilemessages`

**Checkpoint**: User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 5 - Load the launch catalog from a spreadsheet (Priority: P1)

**Goal**: The admin loads the whole launch catalog once from a staff-filled `.xlsx` workbook; every
problem is reported by sheet, row and column, and products with problems stay unpublished.

**Independent Test**: Import a sample workbook with valid and invalid rows; valid products appear
exactly as described, invalid rows are reported, and a second import is refused.

### Tests for User Story 5 ⚠️

- [X] T078 [P] [US5] Create `tests/fixtures/build_sample_catalog.py` that writes `tests/fixtures/sample_catalog.xlsx` (all eight sheets from contracts/catalog-import.md, valid rows plus one of each invalid case) and generated 2:3 photos in `tests/fixtures/photos/`
- [X] T079 [P] [US5] Write `tests/unit/test_import_row_validation.py`: one test per rule in contracts/catalog-import.md (missing required value, unknown key, bad `size`, `price_rub` ≤ 0, `stock` < 0, `one` mixed with letter sizes, duplicate keys, `fur_treatment_detail_ru` missing when `treated`, missing photo file, bad `publish` value), each producing a Russian message with sheet, row and column
- [X] T080 [P] [US5] Write `tests/unit/test_publishing_rules.py`: publishing fails for each of the five rules in data-model.md "Publish rules" and succeeds when all hold; `first_published_at` is set on the first publish only
- [X] T081 [P] [US5] Write `tests/integration/test_import_catalog.py`: the sample workbook loads every valid category, product, color, variant, photo (with renditions) and size guide; products with problems are drafts and listed in the report; categories with imported products are published; `--dry-run` writes nothing; a missing sheet or column exits 1 before importing; a second run after a completed import exits 1; an unexpected error rolls back everything and marks the import `failed`; `<workbook>-report.csv` has columns sheet, row, column, problem

### Implementation for User Story 5

- [X] T082 [US5] Create `catalog_import/models.py` `CatalogImport`: `started_at` / `finished_at` ("`finished_at` NULL while running"), `status` `running`/`completed`/`failed`, `source_filename`, `run_by` ("FK User, protect"), `products_published` / `products_draft` / `rows_rejected` ("int ≥ 0"), `problems` ("JSONB list of `{sheet, row, column, message}`"); generate `catalog_import/migrations/0001_initial.py`
- [X] T083 [US5] Implement `catalog/services/publishing.py`: `publish(product)` / `unpublish(product)` enforcing the five publish rules in data-model.md and setting `first_published_at` once; raise `PublishRuleError` listing every failed rule
- [X] T084 [P] [US5] Implement `catalog_import/workbook_reader.py`: open the workbook with openpyxl (read-only), require every sheet and column in contracts/catalog-import.md (raise `ImportFormatError` naming what is missing), skip blank rows, and yield rows as dicts with their row numbers
- [X] T085 [US5] Implement `catalog_import/row_validation.py`: one small validator per sheet returning typed rows and `ImportProblem(sheet, row, column, message)` items with Russian messages; convert `price_rub` to kopecks
- [X] T086 [US5] Implement `catalog_import/importer.py` `CatalogImporter`: refuse when a completed import exists; inside one transaction create categories, size guides, product types, products (slugs via `assign_slugs`), category memberships (first key = primary), colors, variants and photos; save a product with problems as an unpublished draft when its Products row has `product_key` and `name_ru`, otherwise skip it; publish products marked `publish = yes` via `publishing.publish` (failures become reported problems); publish categories that received products; record the `CatalogImport` with totals and problems
- [X] T087 [US5] Generate photo renditions for all imported photos in parallel with `ProcessPoolExecutor` before the transaction commits, in `catalog_import/importer.py` (research R12, SC-008)
- [X] T088 [US5] Implement `catalog_import/management/commands/import_catalog.py` with arguments `<workbook.xlsx>`, `--photos`, `--dry-run`, `--run-by`; print the summary; write `<workbook>-report.csv`; exit code 0 when completed (even with rejected rows) and 1 when it could not run
- [X] T089 [US5] Document the workbook format for staff in `catalog_import/WORKBOOK_FORMAT.md` (Russian, copied from contracts/catalog-import.md) and add an empty template workbook `catalog_import/catalog_template.xlsx` with the eight sheets and header rows

**Checkpoint**: The launch catalog can be loaded; US1 and US2 pages show imported products.

---

## Phase 6: User Story 6 - Staff keep the catalog up to date (Priority: P1)

**Goal**: Staff sign in to `/staff/`, edit every catalog record in Russian and English without the
admin's help; every change is recorded with who, when, old and new values, and can be undone;
sign-in is protected by password length, lockout and inactivity timeout.

**Independent Test**: Create a staff account, sign in, change a price, stock, publish status, a
text and a photo; each appears on the shop within 5 minutes and in the change history with who,
when, old and new values; undo the price change.

### Tests for User Story 6 ⚠️

- [X] T090 [P] [US6] Write `tests/integration/test_staff_access.py`: an anonymous request to any `/staff/` URL redirects to sign-in and the response contains no catalog data; a disabled account is refused with the wrong-password message; 5 wrong passwords lock the username for 15 minutes and the correct password is refused while locked; success resets the counter; a session ends after 2 hours without requests; a password shorter than 12 characters is rejected; staff (non-superuser) cannot open user screens; nobody can delete a user; `/staff/` responses carry `X-Robots-Tag: noindex`
- [X] T091 [P] [US6] Write `tests/integration/test_change_history.py`: a price change via the admin writes one `updated` record with staff, time, field, old and new value; a photo delete writes a `deleted` snapshot and keeps the files; a product create writes a `created` snapshot; one save shares a `change_set`; bulk publish writes one record per product
- [X] T092 [P] [US6] Write `tests/integration/test_undo.py`: undoing an `updated` record restores the old value and writes a record with `undoes` set; undo is refused when the field has changed since; undoing a `deleted` photo recreates it with its original id; undoing a `created` row deletes it and records each deletion; an undo can itself be undone
- [X] T093 [P] [US6] Write `tests/integration/test_change_history_append_only.py`: raw SQL `UPDATE` and `DELETE` on the change-record table raise an error; setting `staff_id` to NULL on a record older than 3 years succeeds; `anonymise_change_history` nulls `staff_id` only on records older than 3 years
- [X] T094 [P] [US6] Write `tests/integration/test_staff_catalog_editing.py`: renaming a product or category regenerates its slugs and the old address answers 301; uploading a photo creates its renditions; products missing English text appear under the "Missing English" filter; publishing a product that breaks a publish rule shows the failed rule; a published change is visible on the shop page on the next request
- [X] T095 [P] [US6] Write `tests/e2e/test_us6_staff.py`: admin creates a staff account; staff signs in, edits a price, stock, publish status, a description and deletes a photo; staff opens the change history and undoes the price change
- [X] T096 [P] [US6] Write `tests/a11y/test_us6_staff_pages.py`: axe on the staff sign-in page, product list, product edit page and change-history list

### Implementation for User Story 6

- [X] T097 [US6] Configure sign-in protection in `config/settings/base.py`: `AUTH_PASSWORD_VALIDATORS` with `MinimumLengthValidator` (`min_length` 12) and `CommonPasswordValidator`; django-axes installed with `AXES_FAILURE_LIMIT = 5`, `AXES_COOLOFF_TIME = timedelta(minutes=15)`, `AXES_LOCKOUT_PARAMETERS = ["username"]`, `AXES_RESET_ON_SUCCESS = True`, access log disabled, `AxesStandaloneBackend` first in `AUTHENTICATION_BACKENDS`; `SESSION_COOKIE_AGE = 7200`, `SESSION_SAVE_EVERY_REQUEST = True`; secure, HttpOnly, `SameSite=Lax` cookies in `config/settings/prod.py` (research R10)
- [X] T098 [US6] Create `audit/models.py` `ChangeRecord` with every field in data-model.md: `changed_at` ("timestamp, default now", indexed), `staff` ("FK User, nullable, protect"), `change_set` (UUID), `entity_type`, `entity_id` (bigint), `entity_label` ("text, ≤ 200"), `action` (`created`/`updated`/`deleted`), `field_name` ("Required for `updated`; NULL otherwise" as a check constraint), `old_value` / `new_value` (JSONB, nullable), `undoes` ("FK ChangeRecord, nullable"); indexes (entity_type, entity_id, changed_at), (staff_id, changed_at), (change_set)
- [X] T099 [US6] Write `audit/migrations/0002_append_only_trigger.py` with `RunSQL` creating a trigger that rejects `DELETE`, and rejects `UPDATE` "unless the only change is `staff_id` → NULL on a row whose `changed_at` is more than 3 years ago"
- [X] T100 [US6] Implement `audit/recording.py`: `snapshot(instance)` (JSON-safe field values; password hashes replaced by the marker "changed"), `record_update(before, after, staff, change_set)` writing one record per changed field, `record_created(...)`, `record_deleted(...)`
- [X] T101 [US6] Implement `audit/undo.py` `undo(record, staff)` following the Undo rules table in data-model.md, raising `UndoRefused` with a Russian reason when refused, and writing the undo records in one transaction
- [X] T102 [US6] Implement `AuditedModelAdmin` in `audit/admin.py`: load the stored row before saving, record changes for the object, its inlines and its deletes in the same transaction as the save (`save_model`, `save_formset`, `delete_model`, `delete_queryset`), roll the change back if recording fails; plus a read-only `ChangeRecordAdmin` (no add, change or delete; filters item type, staff, date; grouped by `change_set`; staff name shown as "—" when NULL) with a per-record "Undo" POST action
- [X] T103 [US6] Mount the admin at `/staff/` in `config/urls.py` (outside `i18n_patterns`, Russian interface), set site header and title, and add middleware `catalog/middleware.py` that sets `X-Robots-Tag: noindex` on `/staff/` responses
- [X] T104 [P] [US6] Create `catalog/admin/category.py`: list (name RU/EN, position, published, product count), create, edit, publish/unpublish actions that loop over objects, delete refused while the category has products; slugs reassigned on save via `assign_slugs`
- [X] T105 [US6] Create `catalog/admin/product.py`: fieldsets Texts (RU and EN side by side), Fur and materials, Size guide override; ordered inline for category memberships (first = primary), inlines for colors, variants (price entered in rubles, stock) and photos (upload, color, order, alt RU/EN); list filters published, category, product type, "Missing English", sold out; actions Publish selected / Unpublish selected via `publishing.publish` that report each failed rule; no delete; slugs reassigned on save; renditions generated for new or replaced photos
- [X] T106 [P] [US6] Create `catalog/admin/size_guide.py`: `ProductType` admin (name RU/EN, default size guide) and `SizeGuide` admin with `SizeGuideRow` inline (size + five measurements in cm), all on `AuditedModelAdmin`
- [X] T107 [US6] Create `catalog/admin/staff_accounts.py` replacing the default `User` admin: admin-only access, create staff with name, username and password, disable/enable via `is_active`, no delete action, changes recorded through `AuditedModelAdmin`
- [X] T108 [US6] Write `catalog/migrations/0002_catalog_staff_group.py`: data migration creating the "Catalog staff" group with add/change/view permissions on every catalog model and view permission on `ChangeRecord`, and no user permissions
- [X] T109 [P] [US6] Create `static/css/admin-theme.css` mapping the Django admin's CSS custom properties (colors, fonts, radii) to `tokens.css`, and `templates/admin/base_site.html` loading `tokens.css`, the Manrope fonts and `admin-theme.css`
- [X] T110 [P] [US6] Implement `audit/management/commands/anonymise_change_history.py` (null `staff_id` on records older than 3 years, FR-044) and `catalog/management/commands/purge_login_attempts.py` (delete django-axes attempt records older than 24 hours, research R10)
- [X] T111 [US6] Add every US6 staff-area string to `locale/ru/LC_MESSAGES/django.po` and run `compilemessages`

**Checkpoint**: Staff can maintain the catalog alone; every change is recorded and undoable.

---

## Phase 7: User Story 3 - Filter and sort a category (Priority: P2)

**Goal**: Shoppers narrow a category by sizes and a price range, sort by newest or price, and share
the exact view by its address.

**Independent Test**: With a known product set, apply each filter and sort alone and in
combination; results and order match the expected set, and the copied address reproduces them.

### Tests for User Story 3 ⚠️

- [X] T112 [P] [US3] Write `tests/unit/test_listing_filters.py`: parsing and normalisation per contracts/shopper-routes.md (unknown sizes and non-numeric values dropped, `price_min` > `price_max` swapped, sizes sorted by scale and de-duplicated, defaults omitted, parameter order `size`, `price_min`, `price_max`, `sort`, `page`), and `to_query()` round-trips
- [X] T113 [P] [US3] Write `tests/integration/test_listing_filtering.py`: size L shows only products with L in stock in at least one color; M + L match either; price range is inclusive on the matching in-stock variant; size + price apply to the same variant; "Price: low to high/high to low" order by the lowest matching in-stock price; sold-out products are excluded while any filter is active and sort last with no filter; offered sizes come only from the category's published products; non-normalised query → 302; no match → "No products match" with a clear-all link; filtered views carry `noindex` and canonical to the unfiltered page; result count shown
- [X] T114 [P] [US3] Write `tests/e2e/test_us3_filters.py` (`js_enabled` and `js_disabled`): apply sizes and a price range, sort, remove one filter, clear all, open the copied address in a new context and see the same results, use browser back/forward
- [X] T115 [P] [US3] Write `tests/a11y/test_us3_filters.py`: axe on a listing with the filter dropdowns open, with active filters, and with the empty state

### Implementation for User Story 3

- [X] T116 [US3] Implement `catalog/services/listing_filters.py`: a `ListingFilters` dataclass with `from_query(querydict)`, `normalised_query()` and `is_active`, plus `Sort` choices `new`, `price_asc`, `price_desc`
- [X] T117 [US3] Extend `catalog/services/listing_query.py` with `filtered_listing(category, filters)`: annotate the minimum price over in-stock variants matching the size filter (`Min` with `filter=Q(...)`), filter the price range on it, exclude sold-out products while filters are active, order by the chosen sort with sold-out products last, and return the sizes available in the category (research R13)
- [X] T118 [US3] Extend `catalog/views/category.py`: parse `ListingFilters`, 302 to the normalised address when it differs, pass filters, offered sizes and active-filter remove links to the template, set `noindex` and canonical for filtered or sorted views
- [X] T119 [P] [US3] Create `templates/components/filter_bar.html`: one GET form with `<details>` dropdowns Size (checkboxes) and Price (from/to inputs in rubles), a sort select, a «Показать» / "Show" submit button and a reset link; HTMX `hx-get`, `hx-trigger="change"` (debounced for price inputs), `hx-select="#results"`, `hx-target="#results"`, `hx-push-url="true"`; CSS section in `static/css/site.css`
- [X] T120 [P] [US3] Create `templates/components/active_filters.html` (one remove link per active filter plus "Clear all", FR-010) and `templates/components/empty_state.html` ("No products match" + clear all, FR-011) with CSS sections in `static/css/site.css`
- [X] T121 [US3] Wrap the result count, active filters, grid, empty state and pagination in `#results` in `templates/catalog/category.html`, keep the count in an `aria-live="polite"` region, and keep focus on the control the shopper used after an HTMX swap
- [X] T122 [US3] Add every US3 interface string to both `locale/*/LC_MESSAGES/django.po` files and run `compilemessages`

**Checkpoint**: Filtering and sorting work with and without JavaScript, and shared addresses
reproduce the view.

---

## Phase 8: User Story 4 - Check the size guide (Priority: P3)

**Goal**: From a sized product page, shoppers open the size guide without leaving the page, compare
measurements in centimetres and inches, read how to measure, and return with their choices kept.

**Independent Test**: Open the size guide from a coat page, check its measurements match the
product's guide, close it and confirm the color and size choices are unchanged; a one-size scarf
shows no selector or guide.

### Tests for User Story 4 ⚠️

- [X] T123 [P] [US4] Write `tests/unit/test_size_guides.py`: `effective_size_guide` prefers the product override over the product type's guide; inches are `cm / 2.54` rounded to one decimal place; rows come in size-scale order
- [X] T124 [P] [US4] Write `tests/integration/test_size_guide_page.py`: a sized product page contains the guide with chest, waist, hips, sleeve and length in cm and inches plus the how-to-measure text in the active language; a one-size product has neither a size selector nor a guide
- [X] T125 [P] [US4] Write `tests/e2e/test_us4_size_guide.py`: with JavaScript, open the guide, close it with Escape and with the close button, focus returns to the "Size guide" button, color and size choices are unchanged; without JavaScript, the guide is readable in a `<details>` element
- [X] T126 [P] [US4] Write `tests/a11y/test_us4_size_guide.py`: axe with the size guide dialog open

### Implementation for User Story 4

- [X] T127 [US4] Implement `catalog/services/size_guides.py`: `size_guide_rows(product)` returning rows in scale order with cm and computed inch values, and the localized how-to-measure text
- [X] T128 [P] [US4] Create `templates/components/size_guide_dialog.html`: a "Size guide" secondary button, a `<dialog>` with a captioned table (one row per size; body and garment measurements in cm and inches) and how-to-measure text, and a `<details>` fallback shown when JavaScript is unavailable; CSS section in `static/css/site.css`
- [X] T129 [P] [US4] Create `static/js/size-guide.js` (ES module, deferred): open with `showModal()`, close on the close button and Escape, return focus to the trigger, and hide the `<details>` fallback when the script runs
- [X] T130 [US4] Include the size guide in `templates/catalog/product.html` next to the size selector only when the product is not one-size and has an effective guide (FR-026, FR-029), and load `static/js/size-guide.js` on product pages only
- [X] T131 [US4] Add every US4 interface string to both `locale/*/LC_MESSAGES/django.po` files and run `compilemessages`

**Checkpoint**: All six user stories are independently functional.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Performance budgets, field metrics, deployment, security and final validation

- [X] T132 [P] Create `field_metrics/models.py` `RumSample` (`received_at`; `metric` `LCP`/`INP`/`CLS`; `value` float; `route` "text, ≤ 50" route name, "never the full URL"; `device_class` `mobile`/`desktop`) with its migration, and `field_metrics/views.py` `POST /rum/` (CSRF-exempt, no cookies, 204 on valid JSON, 400 otherwise) wired in `config/urls.py`
- [X] T133 [P] Vendor `static/vendor/web-vitals.js` and create `static/js/rum.js` sending LCP, INP and CLS with the route name and device class via `navigator.sendBeacon('/rum/')`; include it in `templates/base.html` (research R12; lawyer confirmation pending)
- [X] T134 [P] Implement `field_metrics/management/commands/purge_rum_samples.py` deleting samples older than 90 days, and write `tests/integration/test_rum_endpoint.py` (204 valid, 400 invalid, nothing identifying stored)
- [X] T135 Create `lighthouserc.json` and `budgets.json` for the home, category and product routes (mobile preset): JS ≤ 25 KB, CSS ≤ 30 KB, fonts ≤ 100 KB, images ≤ 200 KB above the fold, LCP ≤ 2500 ms, CLS ≤ 0.1, TBT ≤ 200 ms (research R12); add a `lighthouse` job to `.github/workflows/ci.yml` that seeds the demo catalog and runs `npx @lhci/cli autorun`
- [X] T136 [P] Write `tests/a11y/test_keyboard_only.py`: with the keyboard alone, reach a category, operate the filters and sort, open a product, choose a color and size, open and close the size guide; focus is always visible
- [X] T137 [P] Write `tests/seo/test_sitemap_and_robots.py`: `/sitemap.xml` lists every published category and product in both languages with `hreflang` alternates and no unpublished items; `/robots.txt` disallows `/staff/` and links the sitemap
- [X] T138 [P] Write `tests/integration/test_no_shopper_cookies.py`: home, category, product and 404 responses set no cookies and load no third-party origins (FR-034, Principle VI)
- [X] T139 Harden `config/settings/prod.py`: `SECURE_HSTS_SECONDS` (one year) with subdomains and preload, `SECURE_SSL_REDIRECT`, `SECURE_PROXY_SSL_HEADER`, `SECURE_CONTENT_TYPE_NOSNIFF`, Django 6 CSP middleware with a `default-src 'self'` policy, `ALLOWED_HOSTS` from the environment, and logging that never writes request IP addresses or personal data
- [X] T140 [P] Create `deploy/Dockerfile` (uv-based image, `collectstatic`, Gunicorn) and `deploy/compose.yml` with services `web` and `caddy` and a media volume
- [X] T141 [P] Create `deploy/Caddyfile`: automatic HTTPS, HSTS, reverse proxy to `web`, `/media/` served from the volume with `Cache-Control: public, max-age=31536000, immutable`, rate limit on `/rum/`, and access logs with the `ip_mask` filter (research R17)
- [X] T142 [P] Create systemd units in `deploy/systemd/`: daily timers running `anonymise_change_history`, `purge_login_attempts` and `purge_rum_samples`
- [X] T143 Create `tests/fixtures/build_catalog_200.py` generating a 200-product workbook with photos, and a marked slow test `tests/integration/test_import_timing.py` asserting the import completes in under 15 minutes (SC-008)
- [X] T144 [P] Create `README.md` with what the project is, the stack, and links to `specs/001-product-catalog/quickstart.md` and the plan
- [X] T145 Run every scenario in `specs/001-product-catalog/quickstart.md` (1–19) and all CI checks locally; fix any failure before merge

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies
- **Foundational (Phase 2)**: depends on Setup and blocks every user story
- **User stories (Phases 3–8)**: each depends on Foundational only. Run them in the order listed
  (P1: US1 → US2 → US5 → US6; then P2: US3; then P3: US4) when working alone
- **Polish (Phase 9)**: after the stories you plan to ship. T135 needs US1–US3 pages; T143 needs US5

### User Story Dependencies

| Story | Depends on | Shares files with |
|-------|------------|-------------------|
| US1 Browse (P1) | Foundational | Base for the product and category templates |
| US2 Variants (P1) | Foundational; extends US1's product view and template | `catalog/views/product.py`, `templates/catalog/product.html` |
| US5 Import (P1) | Foundational; its results are visible through US1 | `catalog/services/publishing.py` (created here, reused by US6) |
| US6 Staff (P1) | Foundational; uses `publishing.py` from US5 (T083) | `catalog/admin/*` |
| US3 Filters (P2) | Foundational; extends US1's listing query, view and template | `catalog/services/listing_query.py`, `catalog/views/category.py` |
| US4 Size guide (P3) | Foundational; placed beside US2's size selector | `templates/catalog/product.html` |

Every story is testable on its own data from `catalog/demo_catalog.py` (T027), so no story needs
another story's UI to be tested.

### Within Each User Story

- Tests first; confirm they fail
- Models and migrations → services → views → templates and components → translations
- Finish the story and pass its checkpoint before starting the next

### Parallel Opportunities

- Setup: T004–T010 in parallel after T001–T003
- Foundational: T013–T015 together; T023/T025 with T029, T030, T032–T034; T038–T042 together after T035
- Every story's test tasks (marked [P]) can be written in parallel
- US1: T056–T060 (components) and T063–T064 (SEO) in parallel
- US6: T104, T106, T109, T110 in parallel once T102 is done
- Different stories can run in parallel by different people after Phase 2

---

## Parallel Example: User Story 1

```text
# Tests for US1 together:
Task: "T045 Write tests/integration/test_category_listing.py"
Task: "T046 Write tests/integration/test_product_page.py"
Task: "T047 Write tests/integration/test_language_urls.py"
Task: "T048 Write tests/seo/test_us1_head_and_structured_data.py"
Task: "T049 Write tests/e2e/test_us1_browse.py"
Task: "T050 Write tests/a11y/test_us1_pages.py"

# Components for US1 together:
Task: "T056 product_card.html + product_grid.html"
Task: "T057 category_chips.html + pagination.html"
Task: "T059 product_gallery.html"
Task: "T060 info_accordion.html"
```

## Parallel Example: User Story 6

```text
# After T102 (AuditedModelAdmin):
Task: "T104 catalog/admin/category.py"
Task: "T106 catalog/admin/size_guide.py"
Task: "T109 static/css/admin-theme.css + templates/admin/base_site.html"
Task: "T110 anonymise_change_history + purge_login_attempts commands"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1: Setup
2. Phase 2: Foundational
3. Phase 3: User Story 1
4. **Stop and validate**: quickstart scenarios 1, 2, 17, 18 with `seed_demo_catalog`
5. Demo the browsable bilingual catalog

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. US1 → browse and product pages (MVP)
3. US2 → colors, sizes, availability
4. US5 → real launch catalog loaded
5. US6 → staff maintain the catalog (required before launch)
6. US3 → filters and sort
7. US4 → size guide
8. Polish → budgets, deployment, final validation

The site can launch only after US6 because staff must be able to keep the catalog current.

---

## Notes

- [P] tasks touch different files and do not depend on incomplete tasks
- Quote data-model.md constraints exactly when writing models; they are repeated in the model tasks
- Follow `CLAUDE.md` clean-code rules: small functions, one responsibility per module, no
  commented-out code
- Commit after each task or logical group
- Never add reference-site assets (logo, photos, copy, icons) to the repository
