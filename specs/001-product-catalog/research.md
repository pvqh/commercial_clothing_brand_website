# Research: Product Catalog

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-11-09

This document resolves every open technical question for the product catalog. Each entry records
the decision, why it was chosen, and what else was considered.

The developer knows Python, FastAPI (basics) and PostgreSQL, and is willing to learn HTML and CSS.
The stack below keeps Python and PostgreSQL, keeps JavaScript to a minimum, and swaps FastAPI for
Django for the reasons in R1.

---

## Stack at a glance

| Layer | Choice | One-line reason |
|-------|--------|-----------------|
| Language | Python 3.13 | Already known; supported by every library below |
| Web framework | Django 6.1 (upgrade to 6.2 LTS when it ships, April 2027) | Server-rendered HTML, staff area, sign-in, translations and migrations are built in |
| Database | PostgreSQL 17, managed, hosted in Russia | Already known; 152-FZ data localisation; strong constraints and triggers for the change history |
| Templates | Django templates + a shared component folder | Plain HTML with small template tags; SEO-friendly by default |
| Styling | Plain CSS with custom properties (design tokens) and cascade layers | No build tool to learn; tokens are just CSS variables |
| Interactivity | HTMX 2 + a few lines of plain JavaScript | Partial page updates written as HTML attributes; site still works without JS |
| Images | Pillow (AVIF, WebP, JPEG renditions) | Pure Python; renditions generated on upload |
| Staff area | Django admin, customised and themed from the tokens | Sign-in, permissions, forms and lists already exist and are tested |
| Sign-in protection | Django auth + `django-axes` | Password length, lockout and session timeout through configuration |
| Spreadsheet import | `openpyxl` | Reads `.xlsx` directly; staff already use spreadsheets |
| Tests | pytest + pytest-django, Playwright (Python), axe-core, Lighthouse CI | Same language for unit, integration and browser tests |
| Quality tools | uv, ruff, mypy + django-stubs, pip-audit, gitleaks | Fast, standard, one command each |
| Serving | Gunicorn + Caddy on one VPS in Russia, Docker Compose | Few moving parts; automatic HTTPS |
| CI | GitHub Actions | Repository already lives on GitHub |

---

## R1. Web framework: Django instead of FastAPI

- **Decision**: Django 6.1, run as a single server-rendered application (one codebase, one deploy).
- **Rationale**:
  - The catalog is an HTML website, not a JSON API. The constitution requires server-rendered
    pages readable without JavaScript (Principle IV). Django is built around exactly that.
  - The spec needs a staff area with sign-in, permissions, create/edit forms for about ten kinds of
    records, lists with filters, and account disabling. Django's admin and auth give all of this
    out of the box. With FastAPI each piece (sessions, CSRF protection, password hashing, form
    validation, admin screens, migrations) would have to be chosen, wired up and secured by hand.
    That is a lot of security-sensitive glue for a developer still learning the basics.
  - Russian/English translation of interface text and language-prefixed URLs (`/en/...`) are built
    in (`i18n_patterns`, `gettext`).
  - Python knowledge transfers directly: views are Python functions, models look like Pydantic or
    SQLAlchemy classes, and the ORM speaks PostgreSQL fluently.
  - Django 6.x adds a built-in Content Security Policy middleware (needed for checkout, Principle
    III) and template partials (which pair well with HTMX).
  - Version: Django 6.1 is the current release (5 August 2026, patch 6.1.1). Upgrade to 6.2 LTS when
    it ships in April 2027 for three years of security fixes.
- **Alternatives considered**:
  - *FastAPI + Jinja2 + SQLAlchemy + Alembic*: familiar, but every staff-area screen, form and
    security control would be custom code. Rejected for scope and risk.
  - *FastAPI API + React/Next.js frontend*: two codebases, a new language (TypeScript), and
    server-side rendering would still be needed for SEO. Rejected as far too much for one developer.
  - *Django 5.2 LTS*: stable, but lacks the 6.x CSP middleware and template partials, and its
    support ends in April 2028 anyway. Rejected in favour of 6.1 → 6.2 LTS.
  - *Future note*: if a JSON API is ever needed (for example, a mobile app), **Django Ninja** adds
    FastAPI-style typed endpoints to the same Django project, so the FastAPI experience still pays
    off.

## R2. Database and hosting location

- **Decision**: PostgreSQL 17 as a managed service from a Russian cloud provider (for example
  Yandex Cloud or Selectel), in the same region as one application VPS. Development and CI use
  PostgreSQL 17 in Docker.
- **Rationale**: Already known. Staff names and accounts are personal data, which 152-FZ requires
  to be stored in Russia (Principle VI). A managed database handles automated backups,
  point-in-time recovery and minor upgrades, which is the hardest part of running a database for a
  solo developer. PostgreSQL triggers, check constraints and JSONB make the append-only change
  history (R9) enforceable in the database itself, not only in code.
- **Alternatives considered**: PostgreSQL inside Docker Compose on the VPS with nightly `pg_dump`
  (cheaper, but restores and upgrades are on you; acceptable fallback). SQLite (no concurrent
  writes from several staff, no triggers of the same strength). Hosting outside Russia (breaks
  152-FZ localisation).
- **Open**: the provider is picked at deployment time on price; nothing in the code depends on it.

## R3. Page rendering and interactivity

- **Decision**: Every shopper page is fully rendered on the server by Django templates. Links and
  forms work without JavaScript. HTMX 2 progressively enhances three things: applying filters and
  sort, changing page, and choosing a color, each by fetching the new page and swapping only the
  changed region while updating the address (`hx-get`, `hx-select`, `hx-push-url`). A small plain
  JavaScript module opens and closes the size guide `<dialog>`.
- **Rationale**:
  - Principle IV (content without JS) and FR-014 (state in the address) come for free when filters
    are an ordinary GET form and colors are ordinary links (`?color=<id>`).
  - SC-007 (results within 1 second): swapping only the results region avoids re-downloading and
    re-laying out the whole page.
  - HTMX is written as HTML attributes, so the developer does not need to learn a JavaScript
    framework. It is about 16 KB compressed, inside the JS budget (R12).
  - Accessibility: after a swap, the result count sits in an `aria-live="polite"` region, and focus
    stays on the control the shopper used (FR-033).
- **Alternatives considered**: Full page reloads only (simplest, and the fallback that always works;
  rejected as the only mode because each filter change re-renders the whole page). Hand-written
  `fetch` + `history.pushState` (about the same behaviour, but more JavaScript to own). React, Vue
  or Alpine.js (more JavaScript than the feature needs).

## R4. Styling and design tokens

- **Decision**: Plain CSS. `static/css/tokens.css` is the single token source (color, typography,
  spacing, radius, motion) as CSS custom properties. `static/css/site.css` holds base styles and one
  section per shared component, organised with `@layer reset, base, components, utilities`.
  Mobile-first media queries (`min-width`) only. A stylelint rule rejects raw colors, font families
  and pixel spacing outside `tokens.css`.
- **Rationale**: The developer is learning CSS. Custom properties are standard CSS, so there is no
  preprocessor or build step. One token file satisfies Principle VII, and the Django admin's own
  theme is also driven by CSS custom properties, so the staff area can read the same tokens (R8).
  Two stylesheets are small enough to fit the CSS budget without bundling.
- **Alternatives considered**: Tailwind CSS (needs a Node build step and a second vocabulary on top
  of CSS). Sass (a build step for features plain CSS now has). A CSS framework such as Bootstrap
  (generic look that fights the brand; heavy).
- **Provisional tokens**: the brand guide does not exist yet (constitution
  `TODO(BRAND_GUIDELINES)`). Implementation starts with the contrast-checked tokens in
  [design-reference.md §5](./design-reference.md#5-proposed-design-tokens-provisional), derived from
  the reference site (R19) with a placeholder accent. The values are swapped in once the guide
  arrives. Because every UI value goes through tokens, this is a one-file change. Recorded in the
  plan's Complexity Tracking.

## R5. Shared component library

- **Decision**: Components are Django template files in `templates/components/`, included with
  `{% include ... with ... %}`. The full list (21 components, each mapped to the reference pattern
  it comes from) is in
  [design-reference.md §6](./design-reference.md#6-component-map-reference--our-component-library).
  Each has a matching CSS section in `site.css`. Pages may only be assembled from these components.
- **Rationale**: Principle VII requires one component library. Includes are plain Django with
  nothing extra to learn.
- **Alternatives considered**: `django-cotton` or `django-components` (nicer syntax, but another
  dependency and concept for a first project).

## R6. Translations (Russian default, English secondary)

- **Decision**:
  - *Interface text* (buttons, labels, messages): Django `gettext` with `locale/ru` and `locale/en`
    message files. `LANGUAGE_CODE = "ru"`.
  - *Catalog content*: explicit `_ru` and `_en` columns on each translated field (for example
    `name_ru`, `name_en`). Russian columns are required and English columns are optional. One
    shared model method returns the active-language value, falling back to Russian (FR-036).
  - *URLs*: `i18n_patterns(..., prefix_default_language=False)`, so Russian lives at the root and
    English under `/en/`. Path words are translated (`/katalog/` vs `/en/catalog/`).
  - The language comes only from the URL. No language cookie and no `Accept-Language` redirect, so
    shoppers get no cookies at all (FR-034) and every address is stable and shareable (SC-004).
  - The language switch links to the current object's address in the other language, built from
    that language's slug (FR-025, FR-035).
- **Rationale**: There are exactly two fixed languages. Explicit columns are the simplest thing that
  works, are visible in the Django admin side by side, and are easy to diff for the change history.
- **Alternatives considered**: `django-modeltranslation` (generates the same columns automatically,
  but Django 6.1 support could not be confirmed and the fallback logic it adds is only a few lines;
  revisit if a third language is ever added). `django-parler` (separate translation tables; more
  joins and harder history diffs). A JSONB translations column (harder to require Russian at the
  database level).

## R7. Readable addresses (slugs) and redirects

- **Decision**: Each product and category stores `slug_ru` and `slug_en`. `slug_ru` is the Russian
  name **transliterated to Latin letters** (for example «Шуба из норки» → `shuba-iz-norki`);
  `slug_en` comes from the English name, or from `slug_ru` when English is missing. Slugs are
  regenerated when the name changes, and every previous slug is kept in a redirect table that
  answers with HTTP 301 (FR-025, Principle IV). Clashes get a numeric suffix (`-2`).
- **Rationale**: The clarification asks for Russian addresses in the Russian version. Transliterated
  Latin slugs keep the words Russian while avoiding percent-encoded Cyrillic
  (`%D1%88%D1%83%D0%B1%D0%B0`) when links are pasted into messengers, emails and social media. This
  is common practice on Russian e-commerce sites and is handled well by Yandex.
- **Alternatives considered**: Cyrillic slugs (`/каталог/шуба-из-норки/`). Valid and readable in a
  browser address bar, but often turn into long percent-encoded strings when shared. This is a
  one-function change if the brand prefers it, so it is flagged for confirmation rather than
  blocking.
- **Query parameters** (`size`, `price_min`, `price_max`, `sort`, `page`, `color`) use the same
  Latin names in both languages. They are controls, not readable text, and filtered views are not
  indexed (R11).

## R8. Staff area: customised Django admin

- **Decision**: The staff area is the Django admin mounted at `/staff/`, in Russian, with:
  - an `AuditedModelAdmin` base class that records every save, inline change and delete in the
    change history (R9) in the same database transaction;
  - delete disabled for products and categories (staff unpublish instead); delete allowed for
    photos, variants, colors, category memberships and size-guide rows;
  - a "Missing English" column and filter on products (FR-043);
  - a read-only change-history list with an "Undo" action (FR-042);
  - a theme stylesheet that sets the admin's CSS custom properties from `tokens.css`;
  - two roles: the admin is a Django superuser; staff are active `is_staff` users in one
    "Catalog staff" group with full catalog permissions and no user-management permissions
    (spec: one staff level).
- **Rationale**: About ten record types need list, create, edit, inline editing (variants, photos)
  and validation. The admin provides all of it, is responsive, ships Russian translations, and has
  had years of accessibility work. Building the same screens by hand would be most of the
  feature's effort.
- **Alternatives considered**: Custom staff screens built from the shopper component library (fully
  satisfies Principle VII, but roughly triples the staff-area work; revisit in roadmap step 4,
  "Admin and inventory", when order handling needs custom screens anyway). Wagtail or another CMS
  (built for page content, not variant/stock data; a large dependency).
- **Constitution impact**: The admin keeps its own markup and component set, so Principle VII
  ("compose UI from the shared component library") is only partly met. This is a time-boxed
  exception in the plan's Complexity Tracking. WCAG 2.2 AA (Principle II) is **not** relaxed:
  staff-area templates are included in the automated axe checks, and any violation is fixed with a
  template override.

## R9. Change history and undo

- **Decision**: An `audit` app owns one append-only `ChangeRecord` table. Each edit produces one row
  per changed field (`action = updated`, field name, old and new value as JSONB). Creating or
  deleting a row produces one record holding a full snapshot (`created` / `deleted`). All records
  from one staff save share a `change_set` id so the history shows them together.
  - **Writing**: `AuditedModelAdmin` reads each object's stored values before saving, compares them
    with the new values, and writes the records in the same transaction. Admin bulk actions such as
    "Publish selected" loop over objects instead of using `queryset.update()`, so nothing bypasses
    the history.
  - **Undo**: For `updated`, the old value is restored only if the field still holds the record's
    new value. Otherwise staff see "This value has changed since; undo the later change first", so a
    newer price is never silently overwritten. For `deleted`, the row is recreated with its
    original id from the snapshot. For `created`, the row (and its children) is deleted, and each
    deletion is recorded as a snapshot so it can itself be undone. Every undo is a new record with
    `undoes` pointing at the original (FR-042).
  - **Append-only in the database**: A PostgreSQL trigger rejects `DELETE` and every `UPDATE` on
    the table except one: setting `staff_id` to NULL on rows older than three years. The admin also
    shows the table read-only (FR-041).
  - **Three-year name removal**: A daily `manage.py anonymise_change_history` (run by a systemd
    timer) nulls `staff_id` on records older than three years (FR-044). Accounts are disabled
    (`is_active = False`), never deleted.
  - **Photos**: Deleting a photo removes its database row but never its files, so undo can bring
    it back.
- **Rationale**: Per-field records map one-to-one to the spec's Change Record entity ("which value,
  old and new"), and undo becomes a single assignment. Database enforcement means a bug or a
  console session cannot quietly rewrite history (Principle VIII).
- **Alternatives considered**: `django-simple-history` (stores whole-row snapshots; per-field
  old/new and single-field undo would need diffing at read time, and its revert restores the whole
  object, clobbering unrelated later edits). `django-reversion` (same whole-object model). Database
  triggers that write the history (cannot know which staff member is acting without passing session
  variables; harder to debug).

## R10. Staff sign-in protection

- **Decision**: Django auth with:
  - `MinimumLengthValidator(min_length=12)` plus Django's common-password validator (FR-040);
  - `django-axes` (9.x, supports Django 6.1): `AXES_FAILURE_LIMIT = 5`,
    `AXES_COOLOFF_TIME = 15 minutes`, `AXES_LOCKOUT_PARAMETERS = ["username"]`,
    `AXES_RESET_ON_SUCCESS = True`, access log disabled. Locked accounts are refused even with the
    right password (spec US6-8);
  - `SESSION_COOKIE_AGE = 7200` with `SESSION_SAVE_EVERY_REQUEST = True`, which gives a two-hour
    inactivity timeout (FR-040). Session, CSRF and auth cookies are `Secure`, `HttpOnly` where
    possible, and `SameSite=Lax`;
  - disabled accounts (`is_active = False`) are refused by Django's default backend (FR-039).
- **Rationale**: Every rule in the spec becomes configuration, not custom security code.
- **Personal-data note**: `django-axes` stores the failed attempt's username, time and IP address.
  Attempts are deleted on successful sign-in and by a daily purge of anything older than 24 hours.
  **Follow-up**: FR-034's list of personal data should add "failed sign-in attempts (username, IP,
  time), kept at most 24 hours, for account protection". This needs a one-line spec edit; it does
  not block planning.
- **Alternatives considered**: A hand-written lockout model and backend (about 40 lines, but
  security code a beginner should not own when a maintained package exists).

## R11. SEO delivery

- **Decision**:
  - Every listing and product page has a unique `<title>`, meta description, canonical URL, Open
    Graph tags and `hreflang` alternates (`ru`, `en`, `x-default` → `ru`).
  - Product pages include `Product` + `Offer`/`AggregateOffer` JSON-LD (`priceCurrency: "RUB"`,
    availability `InStock` or `OutOfStock`) and `BreadcrumbList` built from the primary category.
  - Filtered, sorted or color-specific views point their canonical at the unfiltered page (keeping
    `page` ≥ 2) and carry `<meta name="robots" content="noindex, follow">`.
  - `django.contrib.sitemaps` produces `/sitemap.xml` with both languages; `/robots.txt` disallows
    `/staff/`.
  - Sold-out products stay HTTP 200 with `OutOfStock` markup. Unpublished products and categories
    return 404 (FR-005).
- **Rationale**: Principle IV, SC-004. Yandex, the main search engine in Russia, reads the same
  schema.org markup, sitemaps and canonical tags.

## R12. Performance budget and images (Principle I)

- **Decision, budget per shopper route** (listing, product), enforced by Lighthouse CI in mobile
  mode with assertions and `budgets.json`:

  | Resource | Budget (compressed) |
  |----------|--------------------|
  | JavaScript | ≤ 25 KB (HTMX ≈ 16 KB + site JS) |
  | CSS | ≤ 30 KB |
  | Fonts | ≤ 100 KB, at most 2 WOFF2 files (Cyrillic + Latin subset) |
  | Images above the fold at 360 px | ≤ 200 KB in total; LCP image ≤ 120 KB |
  | Lab thresholds | LCP ≤ 2.5 s, CLS ≤ 0.1, TBT ≤ 200 ms (lab stand-in for INP) |

  Staff-area routes have no Core Web Vitals gate (internal, not indexed; see Complexity Tracking).
- **Images**: When a photo is uploaded (staff area) or imported, Pillow creates renditions at widths
  360, 720, 1080 and 1440 px (never wider than the original) in AVIF, WebP and JPEG. They are stored
  at predictable paths (`photos/<id>/<width>.<format>`). Templates emit `<picture>` with
  `srcset`/`sizes`, explicit `width`/`height`, `loading="lazy"` below the fold, and
  `fetchpriority="high"` on the LCP image. Caddy serves them with a one-year immutable cache.
  The import generates renditions in parallel (`ProcessPoolExecutor`) to stay within SC-008.
- **Photo standard (provisional)**: **2:3 portrait** for listing cards and product galleries, the
  same crop in both places, full-length model on a plain light grey studio background, at least
  1440 px wide (R19). Pending brand confirmation (Principle VII).
- **Fonts**: **Manrope** (SIL OFL, Cyrillic + Latin), self-hosted as two variable WOFF2 subset
  files (about 70 KB in total) with `font-display: swap`, and the Cyrillic file preloaded. Falls back
  to the system font stack. Replaced if the brand guide names another typeface (R19).
- **Freshness (FR-024)**: Pages are rendered from the database on each request (about 1,000
  products and 20,000 variants is small for PostgreSQL), sent with `Cache-Control: public,
  max-age=60`. Any change reaches shoppers within about a minute, well inside 5 minutes.
- **Field data**: The `web-vitals` library (≈ 2 KB) sends LCP, INP and CLS to a first-party
  `/rum/` endpoint storing only metric name, value, route template and device class. No cookies,
  identifiers or IP addresses are stored. **Lawyer to confirm** this counts as essential under
  152-FZ. If it does not, it loads only after consent once the consent banner exists, and Chrome UX
  Report data is used meanwhile.
- **Alternatives considered**: An on-the-fly image proxy such as imgproxy (less code, but one more
  service to run; good upgrade path if photo volume grows). A CDN (not needed for a
  single-country audience served from a Russian data centre).

## R13. Listing queries: filters, sort, "From" price

- **Decision**: One ORM query per listing page. It annotates each product with the minimum price
  over its **in-stock variants that match the active size filter** (`Min` with a `filter=Q(...)`),
  then filters on that value for the price range and orders by it. Sold-out products (no in-stock
  variant) appear only when no filter is active. Their displayed price is the lowest price of any
  variant, and they sort last in price sorts. Newest sorts by `first_published_at DESC, id DESC`.
  Indexes: `variant(color_id, size) WHERE stock > 0`, `product(is_published, first_published_at)`,
  `product_category(category_id, product_id)`.
- **Interpretation to confirm**: FR-013 says "the product's lowest in-stock variant price". With a
  size filter active, this plan uses the lowest price **among the filtered sizes**, so a shopper
  filtering by L never sees "From" a price that applies only to size S. With no size filter, both
  readings are identical.
- **Single-size rule (FR-029)**: The size selector and size guide are hidden when a product's only
  size is "One size". A coat stocked only in M still shows its selector and guide.
- **Address normalisation**: The view parses the query string into a normalised filter object.
  Unknown sizes and invalid numbers are dropped, min > max is swapped, and a page beyond the last
  becomes the last page. If the normalised address differs from the requested one, it answers
  302 → normalised address (spec edge cases), so every shared link has one canonical form.

## R14. Launch catalog import

- **Decision**: `manage.py import_catalog <workbook.xlsx> --photos <folder>` reads a workbook with
  one sheet per entity using `openpyxl` (format in
  [contracts/catalog-import.md](./contracts/catalog-import.md)). It:
  - checks every row and collects problems as (sheet, row number, column, message in Russian);
  - with `--dry-run`, only reports, so staff can fix the spreadsheet before the real run;
  - saves a product with problems as an unpublished draft when its own Products row is usable, so
    staff can complete it in the staff area, and skips it otherwise;
  - records a `CatalogImport` with counts and the full report, and writes the report as a CSV next
    to the workbook;
  - refuses to run when a completed import already exists ("one-time", FR-032).
- **Rationale**: SC-008 needs actionable, row-level reasons. A dry run lets staff iterate without
  the admin cleaning up partial imports. A management command needs no UI and is run by the admin,
  who is the developer.
- **Alternatives considered**: A CSV per entity (staff would juggle six files; `.xlsx` keeps them in
  one workbook). An upload screen in the staff area (unnecessary for a one-time admin task). The
  `pandas` library (heavy for row-by-row validation).

## R15. Money

- **Decision**: Prices are stored as integer **kopecks** (`PositiveBigIntegerField`), entered and
  shown in whole rubles, and formatted Russian-style in both languages (`125 000 ₽`). The
  spreadsheet and the price filter use whole rubles.
- **Rationale**: Principle V forbids floats for money. Integer minor units are the simplest exact
  type.

## R16. Testing strategy and CI gates

- **Decision**:
  - **Unit** (pytest): filter normalisation, price selection, slug transliteration and redirects,
    fallback-to-Russian, change-record diffing, undo conflict rules, import row validation.
  - **Integration** (pytest-django against real PostgreSQL 17): listing queries, append-only
    trigger, admin save → change records, lockout and session timeout, import of a sample
    workbook.
  - **End-to-end** (Playwright for Python): one test per user story's acceptance scenarios, with
    JavaScript on and off for browsing, filtering and the product page.
  - **Accessibility**: axe-core injected through Playwright on every shopper template and on the
    staff list, edit, history and sign-in pages. Zero serious or critical violations allowed
    (Principle II). A keyboard-only Playwright pass covers filters, gallery, variants and the size
    guide.
  - **SEO**: tests parse each template's JSON-LD and meta tags and check required properties,
    canonical and `hreflang` (quality gate "Structured-data and meta-tag validation").
  - **Performance**: Lighthouse CI (`@lhci/cli`, Node used in CI only) against seeded pages with
    the R12 budgets.
  - **Static and security**: ruff (lint + format), mypy with django-stubs, stylelint (token rule),
    pip-audit, gitleaks.
  - All run in GitHub Actions on every pull request with a PostgreSQL 17 service container. Any
    failure blocks merge.
- **Rationale**: One language (Python) for nearly every test. The constitution's quality gates
  each map to one CI job.

## R17. Serving and deployment

- **Decision**: One VPS in Russia running Docker Compose with two services: `web` (Gunicorn
  serving Django, static files through WhiteNoise with compressed, hashed filenames) and `caddy`
  (automatic HTTPS, HSTS, serves `/media/` photos, IP addresses masked in its access log with the
  `ip_mask` log filter). PostgreSQL is the managed service from R2. Photo files live on a mounted
  volume, backed up nightly to object storage at the same Russian provider. A systemd timer on the
  host runs the daily `anonymise_change_history` and attempt-purge commands.
- **Rationale**: The fewest services that meet HTTPS/HSTS (Principle III), Russian data
  localisation (Principle VI) and "no personal data in logs" (Principle VI: IP addresses are
  personal data).
- **Alternatives considered**: Nginx (more configuration for the same result; Caddy gets HTTPS
  certificates automatically). Kubernetes or a platform-as-a-service (unnecessary at this scale).
  Celery + Redis for background work (no workload needs a queue yet: renditions for a single
  upload take a few seconds, and the one-time import runs in parallel processes).

## R18. Tooling

- **Decision**: `uv` for Python versions, dependencies and the lock file. `pyproject.toml` holds
  ruff, mypy and pytest settings. `pre-commit` runs ruff, stylelint and gitleaks locally.
- **Rationale**: `uv` is fast and replaces pip, venv and pip-tools with one tool. It is the
  current standard for new Python projects.

## R19. Visual design direction (reference: mexa-ekaterina.ru)

- **Decision**: Follow the layout language of <https://mexa-ekaterina.ru/>, studied in detail in
  [design-reference.md](./design-reference.md): white space, near-black text, one accent color,
  uppercase labels, pill buttons, radius-10 photo cards, 2:3 studio photos, a dropdown filter bar
  with an apply button, an info panel with accordions on the product page, and a dark footer. The
  provisional tokens and the 21-component library come from that study. The reference's own assets
  (logo, monogram, photos, copy, icons) and its red accent are **not** reused.
- **Deliberate differences**: mobile-first CSS with 3 breakpoints instead of about 15 desktop-first
  ones; no jQuery carousels (CSS scroll-snap instead); flat categories instead of a nested tree;
  colors as variants of one product instead of separate products; regular-weight body text instead
  of light grey text; control borders and meta text at WCAG AA contrast; alt text, `srcset` and lazy
  loading on every photo; no third-party trackers or widgets, and no "continuing means consent"
  banner.
- **Rationale**: The brand chose this site as its design example. Its structure suits fur coats
  (tall photos, calm surfaces). The study also exposed accessibility, performance and privacy
  problems that our constitution forbids (Principles I, II, VI). Copying another fur retailer's
  marks or look in the same market would invite confusion and legal risk.
- **Alternatives considered**: A generic e-commerce theme (does not match the brand's chosen
  direction). Copying the reference's palette and monogram style (rejected for trademark and
  unfair-competition risk; the brand supplies its own).

---

## Follow-ups (do not block planning)

1. **Spec FR-034**: add failed sign-in attempts as transient personal data (R10).
2. **Brand**: confirm transliterated Russian slugs (R7) and the 2:3 photo standard (R12), and
   supply the brand guide (accent color, logo, typeface if not Manrope) so placeholder tokens can be
   replaced (R4, R19).
3. **Spec FR-013**: confirm the filtered "From" price reading (R13).
4. **Lawyer**: confirm the anonymous first-party performance beacon (R12) and the staff
   personal-data handling (Principle VI).
5. **Brand, from the design study** ([design-reference.md §7](./design-reference.md#7-decisions-for-the-brand)):
   letter sizes vs Russian numeric sizes, a fur-type filter, a product article number, and the
   brand's accent color and logo. **Deferred by the brand (2026-11-09)**: each will come as a later
   spec change. None is in this feature's tasks; placeholders stay until then.

## Sources

- [Django 6.1 released (Django weblog, 5 Aug 2026)](https://djangoproject.com/weblog/2026/aug/05/django-61-released)
- [Django 6.1 release notes](https://docs.djangoproject.com/en/6.1/releases/)
- [django-axes 9.0.0 release](https://newreleases.io/project/pypi/django-axes/release/9.0.0)
- [django-modeltranslation on PyPI](https://pypi.org/project/django-modeltranslation/)
