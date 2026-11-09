# Implementation Plan: Product Catalog

**Branch**: `001-product-catalog` | **Date**: 2026-11-09 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-product-catalog/spec.md`

## Summary

A bilingual (Russian first, English second) catalog for a fur-coat brand. Shoppers browse flat
categories, filter by size and price, sort, and open product pages with per-color galleries,
per-variant stock and a size guide. Staff maintain the catalog in a staff-only area where every
change is recorded and undoable. The admin loads the launch catalog once from a spreadsheet.

**Technical approach**: one server-rendered **Django 6.1** application on **Python 3.13** and
**PostgreSQL 17**, hosted in Russia. Pages are plain HTML from Django templates, styled with plain
CSS driven by one design-token file, and progressively enhanced with **HTMX** for filter, sort,
pagination and color changes without full reloads. The staff area is a customised **Django admin**
with an append-only change history (enforced by a database trigger) and per-field undo. Photos are
turned into AVIF/WebP/JPEG renditions with **Pillow**. The full reasoning for every choice, including
why Django replaces FastAPI, is in [research.md](./research.md).

**Visual direction**: modelled on the layout language of mexa-ekaterina.ru, which the brand chose as
its example. It is quiet and premium, with Manrope type, one accent color, pill buttons, 2:3 studio
photos and a dark footer. Our accessibility, performance and privacy rules override the reference
where it falls short. Sections, components, tokens and the image inventory are in
[design-reference.md](./design-reference.md) (research R19).

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Django 6.1 (→ 6.2 LTS, April 2027), psycopg 3, django-axes 9, Pillow
(AVIF), openpyxl, WhiteNoise, Gunicorn, HTMX 2 (vendored static file), web-vitals (vendored)

**Storage**: PostgreSQL 17 (managed, Russian region); photo files on a mounted volume, backed up to
object storage at the same provider

**Testing**: pytest + pytest-django (unit, integration on real PostgreSQL), Playwright for Python
(end-to-end), axe-core via Playwright (accessibility), Lighthouse CI (performance budgets), ruff,
mypy + django-stubs, stylelint, pip-audit, gitleaks

**Target Platform**: Linux VPS in Russia (Docker Compose: Gunicorn + Caddy); shoppers on mobile and
desktop browsers, 360 px first

**Project Type**: Web application, a single server-rendered Django project (no separate frontend)

**Performance Goals**: Core Web Vitals "good" at p75 on mobile (LCP ≤ 2.5 s, INP ≤ 200 ms,
CLS ≤ 0.1; SC-002); filter results within 1 s for 95% of attempts (SC-007); shopper-visible changes
within 5 minutes (FR-024; design gives ≤ 60 s); 200-product import in under 15 minutes (SC-008)

**Constraints**: Content readable without JavaScript; per-route budgets JS ≤ 25 KB, CSS ≤ 30 KB,
fonts ≤ 100 KB, above-the-fold images ≤ 200 KB (research R12); WCAG 2.2 AA on shopper and staff
pages; no shopper cookies or personal data; staff personal data stored in Russia; no IP addresses
in logs

**Scale/Scope**: About 1,000 products and 20,000 variants in year one; a handful of staff accounts;
3 shopper page types, about 8 staff screens, 1 import command

No item remains NEEDS CLARIFICATION. Interpretations that the brand should confirm are listed under
"Follow-ups" in [research.md](./research.md#follow-ups-do-not-block-planning).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution version 2.0.0.

| Principle | Status | How this plan complies |
|-----------|--------|------------------------|
| I. Mobile-First & Fast | ✅ shopper pages / ⚠️ staff area | Shopper templates and CSS are written 360 px first with `min-width` queries. The per-route budget is declared (R12) and enforced by Lighthouse CI. Images use `<picture>` with AVIF/WebP/JPEG `srcset`/`sizes`, explicit dimensions and lazy loading. The staff area (Django admin) is responsive but was not designed mobile-first and has no CWV gate: **exception 1** |
| II. Accessible (WCAG 2.2 AA) | ✅ | axe in CI on every shopper template **and** the staff sign-in, list, edit and history pages, with zero serious/critical violations. Keyboard-only Playwright pass. Out-of-stock and selected states in text and `aria-current`/`disabled`. Alt text required by the database and by import validation. Size guide in a modal `<dialog>` with focus return. Targets ≥ 24×24 px via tokens |
| III. No Raw Card Data | ✅ n/a | No payments in this feature. HTTPS + HSTS through Caddy from day one. Django 6.x CSP middleware is available for checkout |
| IV. SEO-Friendly Pages | ✅ | Server-rendered HTML; unique title/description/canonical/OG/hreflang; `Product`/`Offer` + `BreadcrumbList` JSON-LD; transliterated stable slugs with 301 on rename; filtered views `noindex` with canonical to the base page; automatic sitemap and robots.txt; sold-out pages stay 200 with `OutOfStock` ([contracts/shopper-routes.md](./contracts/shopper-routes.md)) |
| V. Tested Cart & Checkout | ✅ n/a | No cart in this feature. Money stored as integer kopecks (R15). The spec records the handoff: orders use server prices and flag recent price changes. ChangeRecord timestamps make "recent price change" queryable |
| VI. Privacy (152-FZ) | ✅ | Shoppers: no cookies, no personal data, no tracking. The RUM beacon stores no identifiers (lawyer to confirm, R12). Staff personal data (name, username, password hash) in PostgreSQL in Russia, encrypted in transit (TLS) and at rest (provider disk encryption). Names removed from history after 3 years. Login attempts purged after 24 h. Caddy masks IPs in logs; no personal data in error reports. Hosting provider added to the processor register. Spec follow-up: list login attempts in FR-034 (R10) |
| VII. Brand-Consistent Design | ⚠️ | One token source (`static/css/tokens.css`), enforced by stylelint; shopper UI composed only from the 21 components in `templates/components/` ([design-reference.md §6](./design-reference.md#6-component-map-reference--our-component-library)); provisional 2:3 photo standard. **Exception 2**: the brand guide does not exist yet, so planning proceeds with provisional tokens drawn from the design study and a placeholder accent. **Exception 3**: the staff area uses the Django admin's own components (themed from the tokens) instead of the shared library |
| VIII. Accountable Staff Access | ✅ | Admin-created accounts only; disable, never delete; append-only ChangeRecord enforced by a PostgreSQL trigger; every staff save recorded in the same transaction; every record undoable, and undos recorded (R9, [contracts/staff-area.md](./contracts/staff-area.md)) |

| Gate / workflow rule | Status | Notes |
|----------------------|--------|-------|
| Lint, types, tests in CI | ✅ | ruff, mypy, pytest (unit, integration, e2e) in GitHub Actions |
| Performance budgets | ✅ | Lighthouse CI with `budgets.json` |
| Accessibility checks | ✅ | axe via Playwright |
| Structured data and meta validation | ✅ | Dedicated pytest suite parsing JSON-LD and head tags |
| Dependency scan | ✅ | pip-audit (and `npm audit` for the CI-only Node tools) |
| Secret scan | ✅ | gitleaks in CI and pre-commit; `.env` git-ignored |
| Russian legal compliance | ✅ | Spec states 152-FZ and Article 10.1 (Russian first, English as an equivalent duplicate). Chestny ZNAK and 54-FZ are out of scope here |
| Roadmap order | ✅ | Feature 1. The spec records the justified deviation of moving staff editing forward from step 4 |
| Code standards (CLAUDE.md) | ✅ | Small modules per concern (see structure); services separate from views; no comments-as-crutch |

**Gate result: PASS**, with three time-boxed exceptions justified in Complexity Tracking.

**Post-design re-check (after Phase 1)**: The data model, contracts and quickstart introduce no new
violations. The trigger-enforced history, explicit `_ru`/`_en` columns, kopeck prices, `noindex`
on filtered views and cookie-free shopper pages all reinforce the checks above. Result unchanged:
**PASS**.

## Project Structure

### Documentation (this feature)

```text
specs/001-product-catalog/
├── plan.md              # This file
├── research.md          # Stack decisions and reasons (Phase 0)
├── data-model.md        # Entities, rules, states (Phase 1)
├── quickstart.md        # Run and validation guide (Phase 1)
├── design-reference.md  # Study of mexa-ekaterina.ru: sections, components, tokens, image inventory
├── contracts/
│   ├── shopper-routes.md    # Public pages, query params, status codes, SEO elements
│   ├── staff-area.md        # Roles, sign-in rules, screens, history and undo
│   └── catalog-import.md    # Import command and workbook format
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit-tasks; not created here)
```

### Source Code (repository root)

```text
pyproject.toml               # dependencies, ruff, mypy, pytest settings
uv.lock
manage.py
.env.example
config/
├── settings/                # base.py, dev.py, test.py, prod.py
├── urls.py                  # i18n_patterns: Russian at root, English under /en/
└── wsgi.py
catalog/                     # shopper-facing catalog
├── models/                  # category.py, product.py, color_variant.py, photo.py, size_guide.py,
│                            #   slug_redirect.py, choices.py, translated.py, timestamped.py
├── services/                # listing_filters.py, listing_query.py, product_availability.py,
│                            #   size_guides.py, slugs.py, publishing.py,
│                            #   photo_renditions.py + rendition_files.py (pure Pillow, runs in worker processes)
├── views/                   # home.py, category.py, product.py, errors.py, robots.py and their helpers:
│                            #   addresses.py, caching.py, pagination.py, slug_lookup.py
├── seo/                     # structured_data.py, sitemaps.py
├── admin/                   # staff-area screens: category, product (+ color/variant), size_guide,
│                            #   staff_accounts, publishing_actions, labelled_inline
├── templatetags/            # localized field, price, picture tags
├── management/commands/     # seed_demo_catalog, purge_login_attempts
├── demo_catalog.py          # record builders shared by tests and seed_demo_catalog
├── staff_group.py           # the "Catalog staff" group and its permissions
├── middleware.py            # staff area: Russian only, X-Robots-Tag noindex
├── context_processors.py    # header/footer navigation
└── urls.py
audit/                       # change history
├── models.py                # ChangeRecord
├── recording.py             # diff and write records
├── undo.py                  # undo rules
├── admin.py                 # AuditedModelAdmin, read-only history with Undo
├── migrations/              # includes the append-only trigger
└── management/commands/anonymise_change_history.py
catalog_import/              # one-time launch import
├── workbook_reader.py       # sheets and columns → SheetRow
├── row_fields.py            # typed reading of one row, reporting each bad value
├── row_validation.py        # one validator per sheet → ValidatedCatalog
├── validated_rows.py        # typed rows ready to save
├── problems.py              # ImportProblem, ProblemLog
├── catalog_writer.py        # saves the rows; renditions in parallel
├── importer.py              # CatalogImporter.check / run
├── models.py                # CatalogImport
├── WORKBOOK_FORMAT.md       # staff-facing format guide (Russian)
├── catalog_template.xlsx    # empty workbook to fill in
└── management/commands/import_catalog.py
field_metrics/               # RUM beacon endpoint, RumSample, purge_rum_samples
templates/
├── base.html
├── components/              # shared component library (Principle VII), 21 files:
│                            #   site_header, site_footer, language_switch, breadcrumbs,
│                            #   section_heading, button, icon, picture, price,
│                            #   product_card, product_grid, category_chips, filter_bar,
│                            #   active_filters, pagination, empty_state, product_gallery,
│                            #   color_options, size_selector, info_accordion, size_guide_dialog
├── catalog/                 # home, category, product, 404
└── admin/                   # staff-area overrides and theme hook
static/
├── css/                     # tokens.css (design-reference §5), site.css, admin-theme.css
├── fonts/                   # manrope-cyrillic.woff2, manrope-latin.woff2 (variable, SIL OFL)
├── icons/                   # sprite.svg (Lucide subset, ISC licence)
├── img/                     # placeholder-2x3.svg, logo placeholder until the brand guide
├── js/                      # size-guide.js, rum.js
└── vendor/                  # htmx.min.js, web-vitals.js
locale/                      # ru/, en/ interface translations
tests/
├── unit/
├── integration/
├── e2e/
├── a11y/
├── seo/
└── fixtures/                # sample_catalog.xlsx; photos/ generated grey 2:3 images (no third-party assets)
deploy/
├── Dockerfile
├── Dockerfile.caddy         # Caddy with the rate-limit module
├── compose.yml              # web + caddy (production)
├── compose.dev.yml          # local PostgreSQL 17
├── Caddyfile
└── systemd/                 # daily anonymise + purge timers
.github/workflows/ci.yml
lighthouserc.json
budgets.json
.stylelintrc.json
.pre-commit-config.yaml
```

**Structure Decision**: One Django project at the repository root with four apps, one per reason
to change: `catalog` (what shoppers see and staff edit), `audit` (change history and undo),
`catalog_import` (the one-time load), and `field_metrics` (performance beacon). There is no separate
frontend, because pages are server-rendered and HTMX is a static file. Tests are grouped by kind so
each CI gate runs one folder.

**After implementation** (2026-11-09): the tree above is what was built. Two documents now sit
outside this feature folder and cover the codebase as a whole:

- [`docs/architecture-review.md`](../../docs/architecture-review.md) records the post-implementation
  review: clean-up items, the deepening backlog AR01–AR09, and a "where new code goes" table.
- [`GLOSSARY.md`](../../GLOSSARY.md) fixes the domain words.

The review found no need to restructure the apps or folders.

## Complexity Tracking

| Exception | Why needed | Simpler alternative rejected because | Time-box |
|-----------|------------|--------------------------------------|----------|
| 1. Principle I: the staff area is responsive but not designed mobile-first and has no Core Web Vitals gate | The Django admin provides sign-in, permissions, forms, inlines and lists for ten record types at almost no cost | Custom mobile-first staff screens would roughly triple the staff-area work. The pages are internal and not indexed, and staff mainly use desktops | Re-evaluate in roadmap step 4 (Admin and inventory) |
| 2. Principle VII `TODO(BRAND_GUIDELINES)`: planning before the brand guide and token source exist | The catalog is the first feature, and the brand guide is still being prepared | Waiting would block all work. Because every UI value already goes through `tokens.css`, swapping placeholder values for brand values is a one-file change | Brand tokens and photo standard confirmed **before this feature's production release** |
| 3. Principle VII: the staff area uses Django admin components, not the shared component library | Same as exception 1 | Same as exception 1. The admin is themed from the same tokens, so colors and typography still match the brand | Re-evaluate in roadmap step 4 |
