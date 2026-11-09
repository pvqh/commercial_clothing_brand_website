# Architecture review: November 2026

This review covers the state of `001-product-catalog` after all 145 tasks were finished (branch
`001-product-catalog`, commit `45a6494`). Domain words follow [`GLOSSARY.md`](../GLOSSARY.md).
Architecture words follow the deep-module vocabulary:

- **Module**: anything with an interface and an implementation.
- **Depth**: how much behaviour sits behind a small interface.
- **Shallow module**: one whose interface is almost as big as its implementation.
- **Seam**: a place where behaviour can be swapped without editing callers.
- **Adapter**: one implementation plugged into a seam.
- **Leverage**: what callers gain from a single interface.
- **Locality**: how far a change has to travel through the code.

## 1. Verdict

**No restructure.** The project layout is sound:

- There are four Django apps: `catalog`, `audit`, `catalog_import` and `field_metrics`. Each has one reason to change.
- Inside `catalog`, models, services, views, seo, admin and templatetags are split by kind. Files are small; the largest Python module is 344 lines.
- The tests are grouped by kind, and each CI job runs one group of folders.

What needs work is **locality**. A handful of business rules are each written in three to six
places, in different idioms: SQL annotations, Python properties, admin filters and import checks.
None of the copies are wrong today, but they will drift the first time one of these rules changes.

Fix this with targeted deepening (§3), not by moving folders. There is also some local clutter
and a version-control gap to clean up first (§2).

## 2. Clean-up

### 2.1 Local folders to delete

All of these are git-ignored, so deleting them changes nothing in the repository.

| Path | Size | What it is | Action |
|------|------|------------|--------|
| `staticfiles/` | 5.2 MB | `collectstatic` output from the Lighthouse run. Dev and test settings serve static files through finders. | Delete. `collectstatic` rebuilds it. |
| `.lighthouseci/` | 6.3 MB | Old Lighthouse reports. | Delete. CI uploads its own. |
| `media/` | 4.7 MB | Demo photos seeded before the transliteration fix, so they show boxes instead of names. | Delete, then run `manage.py seed_demo_catalog`. |
| `.specify/specs/001-product-catalog/` | 15 KB | A **stale early copy** of `spec.md` and the checklist. It differs from `specs/001-product-catalog/`. | Delete. `.specify/feature.json` already points at `specs/`. |
| `.claude/worktrees/` | empty | Leftover from tooling. | Delete. |

### 2.2 Version-control gap

`.gitignore` ignores the whole of `.specify/` and `.claude/`. As a result, the repository does
**not** contain:

- `.specify/memory/constitution.md`: the governance document that `plan.md`'s Constitution Check is gated on.
- The spec-kit scripts and templates that every `/speckit-*` command runs.
- `.claude/skills/speckit-*`: the project commands themselves.

A second developer, or a fresh clone, can't read the constitution or run the spec workflow.

**Recommended `.gitignore` change** (not applied yet; it's a one-line decision for the owner):

```gitignore
# replace ".claude" and ".specify" with:
.claude/settings.local.json
.claude/worktrees/
```

Then commit `.specify/` (after deleting the stale `specs/` copy inside it), along with
`.claude/skills/` and `.claude/settings.json`.

### 2.3 Dead code

| Where | What | Action |
|-------|------|--------|
| `catalog/views/addresses.py` `query_string()` | Never called. `ListingFilters.query_string` owns this job. | Delete. |
| `catalog/models/color_variant.py` `Color.is_out_of_stock` | Never called. `color_states()` works it out again. | Delete, or make it the single implementation (§3.1). |
| `catalog/services/publishing.py` `unpublish()` | Only tests call it. The admin unpublishes through `publishing_actions.mark_unpublished`. | Route the admin through it (§3.5). |
| `catalog/services/listing_query.py` `published_listing()` | Pass-through with one caller (`home.py`): `filtered_listing(category, ListingFilters())`. | Inline it, or keep it as the home page's name for the rule. Low value either way. |
| `catalog/models/__init__.py` `RENDITION_WIDTHS` export | Nothing imports it from the package. | Drop it from `__all__`. |

### 2.4 Test duplication

The `category` fixture is defined in six test files with the same body, and `product`/`coat`
fixtures repeat in two or three. Move them into `tests/conftest.py`, or into the conftest of the
folder that uses them.

## 3. Deepening candidates

Ranked by recommendation strength. Each one keeps behaviour the same and covers it with the
existing tests.

### 3.1 Stock and price facts → one module. **Strong**

**Files:**
- `catalog/services/listing_query.py` (`with_card_prices`)
- `catalog/services/product_availability.py` (`price_range_of`, `color_states`)
- `catalog/models/product.py` (`is_sold_out`)
- `catalog/models/color_variant.py` (`Color.is_out_of_stock`)
- `catalog/admin/product.py` (`SoldOutFilter`, `ProductAdmin.in_stock`)
- `catalog/seo/structured_data.py` (reads `PriceRange.sold_out`)

**Problem.** "In stock", "sold out" and "the in-stock price range, else the full range" are each
implemented several times:

- In SQL: `Min`, `Max` and `Coalesce` in `with_card_prices`, and `Exists` in `SoldOutFilter`.
- In Python: `price_range_of`, `is_sold_out`, `color_states` and `Color.is_out_of_stock`.

That makes six implementations of one rule. A change to it, for example "reserved stock doesn't
count", has to find all six. Only the listing's version is covered by the filter tests.

**Solution.** Give the rule one home: a custom `ProductQuerySet` / `VariantQuerySet` in
`catalog/models/`.
- Expose `with_stock_facts()` (the card-price annotations) and `in_stock()`.
- Build the listing, the product page's `PriceRange`, the admin column and filter, and the JSON-LD
  availability from it.
- Delete `price_range_of`, `Product.is_sold_out` and `Color.is_out_of_stock`.

**Wins:**
- Locality: one rule, one module.
- Leverage: five callers share one interface.
- Tests hit one queryset interface.
- `product_availability.py` shrinks to the view-model dataclasses.

### 3.2 Shopper visibility → model managers. **Strong**

**Files:**
- `catalog/views/home.py`
- `catalog/context_processors.py`
- `catalog/seo/sitemaps.py`
- `catalog/views/slug_lookup.py`
- `catalog/services/listing_query.py` (`filtered_listing`, `offered_sizes`)

**Problem.** "Shopper-visible category" (published, and holding a published product, ordered by
position) is written out three times. "Published product in category X" is written out twice,
with different join paths.

**Solution.** Add `Category.objects.shopper_visible()` and `Product.objects.published()` (and
`.in_category(c)`) on the models, and call them everywhere. Django's canonical idiom for this is
a custom QuerySet.

**Wins:**
- Three copies collapse to one.
- New pages get the visibility rule for free.
- Combines naturally with §3.1 into one `catalog/models/querysets.py`.

### 3.3 Languages and addresses → one module outside `views/`. **Strong** (small)

**Files:**
- `catalog/views/addresses.py`
- `catalog/models/translated.py`
- `catalog/templatetags/catalog_tags.py` (`localized_slug`)
- `catalog/services/slugs.py`
- `catalog/seo/sitemaps.py`
- `catalog/models/slug_redirect.py`
- `config/settings/base.py`

**Problem.**
- The list of languages is written four times, plus the copy in `settings.LANGUAGES`:
  `("ru", "en")` in `addresses.py`, the same tuple in `slugs.py`, `["ru", "en"]` in `sitemaps.py`,
  and the `choices` of `SlugRedirect.language`.
- "Which language is active" is worked out three times with the same expression,
  `(get_language() or "ru").startswith("en")`.
- `seo/sitemaps.py` imports from `views/`, so a non-view module depends on the views package.

**Solution.** Create `catalog/languages.py`:
- `LANGUAGES`, derived from settings.
- `active_language()`.
- Field-name helpers such as `slug_field(language)`.

Move `addresses.py` up to `catalog/addresses.py`.

**Wins:**
- Adding a third language touches one file.
- Sitemaps stop reaching into views.
- Removes three copy-pasted language checks.

### 3.4 Photo renditions → one deep module. **Worth exploring**

**Files:**
- `catalog/services/photo_renditions.py`
- `catalog/services/rendition_files.py`
- `catalog/models/photo.py` (`rendition_widths`, `cropped_width`)
- `catalog/templatetags/catalog_tags.py` (`picture`, `srcset`, `rendition_url`)
- `catalog/views/product.py` (`open_graph_image_path`)
- `catalog_import/catalog_writer.py`

**Problem.** The rendition layout `photos/<id>/<width>.<ext>` is spelled out separately in
`rendition_path`, `rendition_job` (`MEDIA_ROOT / "photos" / pk`) and `rendition_files`
(`f"{width}.{ext}"`). Choosing widths, building URLs and building the srcset are spread across a
model, a template tag and a view. To change the formats or the widths, you have to edit four
modules.

**Solution.** Create a `PhotoRenditions(photo)` module with this interface:
- `widths`
- `url(width, format)`
- `srcset(format)`
- `largest(format, max_width)`
- `job()`

It is the only place that knows the layout. Keep `rendition_files.py` as the pure-Pillow adapter
for that interface. Its seam is real, with two adapters: in-process from the admin, and a
`ProcessPoolExecutor` from the import.

**Wins:**
- The layout is known in one place.
- `picture` and Open Graph share `largest()`.
- The template tag shrinks to markup only.

### 3.5 Audited change and publishing → one path. **Worth exploring**

**Files:**
- `catalog/admin/product.py` (`publish_selected`)
- `catalog/admin/publishing_actions.py`
- `catalog/admin/category.py`
- `catalog/services/publishing.py`
- `audit/admin.py`
- `audit/undo.py`

**Problem.**
- The ritual "`stored_copy` → change → `record_update(before, after, user, change_set_of(request))`"
  is hand-written in `publish_selected`, `set_published`, `save_model` and `save_formset`.
- Publishing exists twice. Products go through `services.publishing.publish`; categories go
  through `mark_published`, and `services.publishing.unpublish` is never used by the admin.
- Turning `entity_type` back into a model is a scan of `apps.get_models()`, written twice (in
  `ChangeRecordAdmin.item_type` and in `undo.model_of`).

**Solution.**
- Add an `audited(obj, staff, change_set)` context manager in `audit/recording.py`.
- Make `catalog/services/publishing.py` own publish and unpublish for both categories and
  products.
- Turn the admin actions into one small factory over those functions.
- Add `audit/entities.py` with `model_for(entity_type)`.

**Wins:**
- Every audited write uses one interface.
- Publishing rules live in the services module only.
- Undo and the history screen share one model lookup.

*Speculative extension:* store `ContentType` instead of the bare model name. That is cheap now,
before launch, but it means a migration on the append-only table.

### 3.6 Import limits derived from the model. **Worth exploring**

**Files:**
- `catalog_import/row_validation.py`
- `catalog/models/*.py`

**Problem.** `row_validation.py` hard-codes more than 20 maximum lengths and required flags
(`PRODUCT_TEXT_COLUMNS`, `max_length=80/60/100/250`) that the models already declare. It also
re-implements three model rules:
- A product can't mix one size with letter sizes (`Variant.clean`).
- Treated fur needs a treatment description (`Product.clean`).
- Two colours of one product can't share a position (a DB constraint).

When someone changes a field's limit in a model, the import silently keeps the old limit.

**Solution.**
- Keep the import's own validator; it gives per-cell messages in Russian.
- Read `max_length` and `blank` from `Model._meta` through
  `RowFields.model_text(Model, field_name)`.
- Turn the three rules into small predicates on the model or the choices (for example
  `Size.mixes(sizes)` and `FurTreatment.needs_detail`). Then `clean()` and the validator call the
  same function.

**Wins:**
- Model and import cannot drift.
- `PRODUCT_TEXT_COLUMNS` becomes a list of column names only.
- About 40 lines of `row_validation.py` go away.

### 3.7 Translation completeness → one rule. **Worth exploring**

**Files:**
- `catalog/models/product.py` (`missing_english`, `missing_russian_fields`)
- `catalog/admin/product.py` (`MissingEnglishFilter`)
- `catalog/services/publishing.py` (`has_russian_texts`)

**Problem.** "Missing English" is written once as a Python property, used by the admin column,
and once as a `Q` chain, used by the admin filter. The two have to agree; no test checks that
they do.

**Solution.** Add `Product.objects.missing_english()` as a queryset in the same
`querysets.py`. The column becomes an annotation, so the filter and the column use one
definition.

**Wins:**
- Filter and column agree by construction.
- The admin list stops running one query per row.

### 3.8 `static/css/site.css` is over 1,000 lines. **Speculative**

The file is 1,077 lines, organised as one section per component, in the same order as
`templates/components/`. Splitting it into separate files would cost either extra requests
(`@import`) or a build step. The project has no CSS build step, and the size budget passes at
5.8 KB compressed.

**Recommendation:** keep one file. If a new component pushes the file past roughly 1,300 lines,
add a concatenation step and split it per component.

## 4. Reviewed and deliberately kept

Future reviews shouldn't re-suggest these. Each has a reason in `research.md`.

- **Django admin as the staff area (R8).** It isn't a custom back office. Nested inlines are
  missing, so variants are edited on the colour page.
- **`_ru` / `_en` columns with a Russian fallback (R6).** No translation tables or packages.
- **Pure-Pillow `rendition_files.py`.** It must not import Django, because import workers run it
  in other processes.
- **Products and categories are never deleted (R8).** `has_delete_permission` returns `False` on
  purpose.
- **The import's own validator, instead of `full_clean()` (R14).** Staff need messages per sheet,
  row and column. §3.6 keeps this and only shares the limits.
- **One view module per page** (`home.py`, `category.py`, `product.py`), with small helper
  modules next to them.
- **`catalog/demo_catalog.py` inside the app package.** Both the tests and the
  `seed_demo_catalog` command use it.

## 5. Suggested order

Each step is small and goes through red → green with the existing suite (`uv run pytest`, then
`uv run pytest tests/e2e tests/a11y`).

| ID | Step | Depends on |
|----|------|------------|
| AR01 | Delete the local clutter (§2.1) and decide the `.gitignore` change (§2.2). | — |
| AR02 | Delete the dead code (§2.3) and move shared fixtures into conftest (§2.4). | — |
| AR03 | Create `catalog/languages.py` and move `addresses.py` up (§3.3). | — |
| AR04 | Create `catalog/models/querysets.py` with shopper visibility (§3.2). | — |
| AR05 | Move the stock and price facts into the querysets and delete the Python copies (§3.1). | AR04 |
| AR06 | Add the missing-English queryset (§3.7). | AR04 |
| AR07 | Create the `PhotoRenditions` module (§3.4). | — |
| AR08 | Add the audited context manager and route publishing through the services module (§3.5). | — |
| AR09 | Derive import limits from the models and share the rule predicates (§3.6). | — |

**Start with AR04 + AR05.** Sold out and price are what shoppers see on every card and every
product page, and those are the rules most likely to change next (reserved stock, sale prices,
the deferred numeric sizes).

## 6. Where new code goes

| New thing | Home |
|-----------|------|
| A rule about which rows shoppers see, or a stock or price fact | `catalog/models/querysets.py` (after AR04) |
| A rule that needs several models or writes a change, such as publishing | `catalog/services/` |
| Something that turns query parameters into state and back | `catalog/services/listing_filters.py` style: a frozen dataclass with `from_query` and `query_string` |
| Language lists, active language, page addresses | `catalog/languages.py`, `catalog/addresses.py` (after AR03) |
| A staff screen | `catalog/admin/<model>.py`, subclassing `AuditedModelAdmin`, and `LabelledTabularInline` for inlines |
| A shopper page | `catalog/views/<page>.py`, wrapped in `@public_cache`, with a template in `templates/catalog/` built from `templates/components/` |
| A new shared UI piece | `templates/components/<name>.html`, plus its own section in `site.css` in the same order |
| An import check | `catalog_import/row_validation.py`, reading limits from the model (after AR09) |
