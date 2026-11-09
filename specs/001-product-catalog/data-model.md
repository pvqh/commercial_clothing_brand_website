# Data Model: Product Catalog

**Feature**: [spec.md](./spec.md) | **Research**: [research.md](./research.md) | **Date**: 2026-11-09

PostgreSQL 17 through the Django ORM. Every table has an `id` (bigint primary key) and, unless
noted, `created_at` / `updated_at` timestamps. A translated field `X` is two columns: `X_ru`
(required unless noted) and `X_en` (optional, falls back to Russian; research R6).

```text
Category ──< ProductCategory >── Product ──< Color ──< Variant
                                   │  │         │
                                   │  │         └──< ProductPhoto (color optional)
                                   │  └──< ProductPhoto
                                   ├── ProductType ── SizeGuide ──< SizeGuideRow
                                   └── SizeGuide (override, optional)

Category ──< CategorySlugRedirect      Product ──< ProductSlugRedirect
StaffMember (Django User) ──< ChangeRecord >── ChangeRecord (undoes)
StaffMember ──< CatalogImport
```

---

## Size (enumeration, not a table)

Stored as a small integer on Variant and SizeGuideRow. Its numeric value **is** the display order
(FR-009).

| Value | Code | Label |
|------:|------|-------|
| 10 | `xxs` | XXS |
| 20 | `xs` | XS |
| 30 | `s` | S |
| 40 | `m` | M |
| 50 | `l` | L |
| 60 | `xl` | XL |
| 70 | `xxl` | XXL |
| 80 | `xxxl` | XXXL |
| 100 | `one` | One size / Единый размер |

The code is used in addresses (`?size=m`) and in the import spreadsheet.

## FurTreatment (enumeration)

`natural` (not dyed or treated), `dyed`, `treated` (other treatment, described in
`fur_treatment_detail`). Labels are translated interface text (FR-016).

---

## Category

A flat group shoppers browse (FR-001). No parent field.

| Field | Type | Rules |
|-------|------|-------|
| name | translated text, ≤ 80 | `name_ru` required |
| slug_ru / slug_en | slug, ≤ 100, each unique | Generated from the name (R7); regenerated on rename |
| position | small int ≥ 0 | Navigation order |
| is_published | bool, default false | Unpublished → 404 and hidden from navigation |

- **Shown in navigation** when `is_published` and it has at least one published product (edge
  case "category has no published products").
- Staff cannot delete a category that has products; they unpublish it.

## CategorySlugRedirect / ProductSlugRedirect

One table per entity, same shape. Records every slug an entity has had (FR-025, Principle IV).

| Field | Type | Rules |
|-------|------|-------|
| category / product | FK, cascade | |
| language | `ru` / `en` | |
| old_slug | slug | Unique per (language, old_slug) |

Written automatically whenever a slug changes. A request to an old slug answers 301 to the
current one.

## ProductType

Groups products that share a size guide, for example "Women's long coats" (FR-028).

| Field | Type | Rules |
|-------|------|-------|
| name | translated text, ≤ 80 | Staff-facing and shown nowhere to shoppers; `name_en` optional |
| size_guide | FK SizeGuide, nullable, protect | Default guide for its products |

## Product

| Field | Type | Rules |
|-------|------|-------|
| name | translated text, ≤ 150 | Required in Russian |
| description | translated long text | Required in Russian |
| care_instructions | translated long text | Required in Russian |
| fur_species | translated text, ≤ 100 | Required in Russian (FR-016) |
| fur_origin_country | translated text, ≤ 100 | Required in Russian |
| fur_treatment | FurTreatment | Required |
| fur_treatment_detail | translated text, ≤ 200 | Required in Russian when `fur_treatment = treated` |
| shell_material | translated text, ≤ 200 | Required in Russian |
| lining_material | translated text, ≤ 200 | Required in Russian |
| trim_material | translated text, ≤ 200 | Optional (blank when there is no trim) |
| product_type | FK ProductType, protect | Required |
| size_guide | FK SizeGuide, nullable, protect | Overrides the type's guide (FR-028) |
| slug_ru / slug_en | slug, ≤ 160, each unique | As Category |
| is_published | bool, default false | |
| first_published_at | timestamp, nullable | Set once, the first time it is published; never reset; drives "Newest" (FR-012) |

**Derived (not stored)**

- `primary_category`: the ProductCategory with `position = 0` (FR-002).
- `effective_size_guide`: `size_guide` if set, else `product_type.size_guide`.
- `is_one_size`: every variant's size is `one` → no size selector or guide (FR-029, R13).
- `is_sold_out`: no variant has `stock > 0` (FR-022).
- `missing_english`: any required translated field, or any related color or photo alt text, has an
  empty `_en` value (FR-043).

**Publish rules** (checked when `is_published` becomes true; staff see each failure as a form
error):

1. At least one category membership (so a primary category exists).
2. At least one color with at least one variant.
3. At least one photo, and every photo has `alt_ru` (FR-017).
4. All required Russian fields filled.
5. Sized products (not `is_one_size`) have an effective size guide.

**States**

```text
Draft (never published) ──publish──▶ Published ──unpublish──▶ Unpublished
                                         ▲                         │
                                         └────────publish──────────┘
```

`first_published_at` is set on the first Draft → Published transition only. Draft and Unpublished
both answer 404 to shoppers. Sold-out is not a state; it is derived from stock and keeps the page
live (HTTP 200).

## ProductCategory

Explicit link table so the primary category and its changes are recorded (FR-002).

| Field | Type | Rules |
|-------|------|-------|
| product | FK, cascade | |
| category | FK, protect | |
| position | small int ≥ 0 | `0` = primary |

Unique (product, category) and unique (product, position).

## Color

| Field | Type | Rules |
|-------|------|-------|
| product | FK, cascade | |
| name | translated text, ≤ 60 | Required in Russian, for example «Натуральный» / "Natural" |
| position | small int ≥ 0 | Unique per product; position 0 is the default selection |

- **Derived** `is_out_of_stock`: no variant of this color has `stock > 0` (FR-021).
- A product with exactly one color shows no color selector (edge case).

## Variant

One buyable size in one color (FR-019).

| Field | Type | Rules |
|-------|------|-------|
| color | FK Color, cascade | The product is `color.product` (no duplicate product column) |
| size | Size | |
| price_kopecks | positive bigint | > 0 (R15) |
| stock | int | ≥ 0 (database check constraint) |

- Unique (color, size).
- A product may not mix `one` with letter sizes (validated on save and import).
- Partial index on (color_id, size) where `stock > 0` for the size filter (R13).

## ProductPhoto

| Field | Type | Rules |
|-------|------|-------|
| product | FK, cascade | |
| color | FK Color, nullable, set null | Empty → shared product photo |
| position | small int ≥ 0 | Gallery order; position 0 of the product is the listing photo |
| original | image file path | JPEG/PNG/WebP, ≥ 1440 px wide recommended |
| width / height | positive int | Of the original; used for `width`/`height` attributes and to choose rendition widths |
| alt_text | translated text, ≤ 250 | `alt_ru` required (FR-017) |

- **Renditions** are files only, at `photos/<id>/<width>.<avif|webp|jpg>` for each width in
  360/720/1080/1440 that is ≤ `width` (R12). Not stored as rows.
- **Gallery for a color**: that color's photos, or the product's shared photos when the color has
  none (edge case).
- Deleting a photo removes the row but keeps its files so undo can restore it (R9).

## SizeGuide

| Field | Type | Rules |
|-------|------|-------|
| internal_name | text, ≤ 100 | Staff-facing, for example "Women's long coats 2026" |
| how_to_measure | translated long text | Required in Russian (FR-027) |

## SizeGuideRow

| Field | Type | Rules |
|-------|------|-------|
| size_guide | FK, cascade | |
| size | Size, excluding `one` | Unique per guide |
| chest_cm, waist_cm, hips_cm | decimal(5,1) | Body measurements, > 0 |
| sleeve_cm, length_cm | decimal(5,1) | Garment measurements, > 0 |

Inches are computed when displayed (`cm / 2.54`, one decimal place), never stored.

---

## StaffMember (Django `User`)

Uses Django's built-in user model. Only the fields below are used; email is left empty because the
spec's personal-data list is name, username and password (FR-034).

| Field | Use |
|-------|-----|
| username | Sign-in name; unique |
| first_name / last_name | The name shown in the change history |
| password | Hashed (Django default PBKDF2 or Argon2); ≥ 12 characters (FR-040) |
| is_active | `false` = disabled; cannot sign in (FR-039) |
| is_staff | `true` for staff and admin |
| is_superuser | `true` only for the admin |

- Staff belong to the "Catalog staff" group (all catalog permissions, no user permissions).
- Accounts are never deleted: the staff area's user screen has no delete action, even for the
  admin (FR-044).
- Lockout state lives in `django-axes` tables (username, IP, time), purged after 24 hours (R10).
- **Personal data**: name and username. Purpose: staff sign-in and change tracing. Legal basis:
  employment. Retention: while employed, then the account is disabled. Stored in Russia
  (Principle VI).

## ChangeRecord (append-only)

One recorded change (FR-041, FR-042, Principle VIII).

| Field | Type | Rules |
|-------|------|-------|
| changed_at | timestamp, default now | Indexed |
| staff | FK User, nullable, protect | Set to NULL after 3 years (FR-044) |
| change_set | UUID | Groups the records from one save or one undo |
| entity_type | text | Model name, for example `product`, `variant`, `productphoto` |
| entity_id | bigint | Id of the changed row |
| entity_label | text, ≤ 200 | Human label at change time, for example "Шуба из норки, Natural / M"; keeps deleted rows readable |
| action | `created` / `updated` / `deleted` | |
| field_name | text, nullable | Required for `updated`; NULL otherwise |
| old_value | JSONB, nullable | `updated`: old field value. `deleted`: full row snapshot |
| new_value | JSONB, nullable | `updated`: new field value. `created`: full row snapshot |
| undoes | FK ChangeRecord, nullable | Set when this record is an undo |

**Database rules**

- A trigger rejects `DELETE`, and rejects `UPDATE` unless the only change is `staff_id` → NULL on a
  row whose `changed_at` is more than 3 years ago.
- A check constraint requires `field_name` exactly when `action = 'updated'`.
- Indexes: (entity_type, entity_id, changed_at), (staff_id, changed_at), (change_set).

**Undo rules** (research R9)

| Original action | Undo does | Refused when |
|-----------------|-----------|--------------|
| updated | Sets `field_name` back to `old_value` | Current value ≠ record's `new_value` |
| deleted | Recreates the row from `old_value` with its original id | A row with that id exists again, or a parent row it needs is gone |
| created | Deletes the row and its children, recording each as `deleted` | The row no longer exists |

Every undo writes new records with `undoes` set and its own `change_set`. Undos can themselves be
undone.

**What is recorded**: every create, field change and delete made in the staff area on Category,
Product, ProductCategory, Color, Variant, ProductPhoto, ProductType, SizeGuide and SizeGuideRow.
Staff account changes made by the admin are recorded the same way, except that password hashes
are stored only as the marker "changed".

## CatalogImport

One spreadsheet load (User Story 5, FR-030, FR-031).

| Field | Type | Rules |
|-------|------|-------|
| started_at / finished_at | timestamp | `finished_at` NULL while running |
| status | `running` / `completed` / `failed` | |
| source_filename | text | |
| run_by | FK User, protect | The admin |
| products_published / products_draft / rows_rejected | int ≥ 0 | Report totals |
| problems | JSONB list of `{sheet, row, column, message}` | Full report (SC-008) |

**States**: `running` → `completed`, or `running` → `failed` (an unexpected error; the whole import
transaction is rolled back). A `completed` import blocks any further import (FR-032).

## RumSample (field performance, research R12)

| Field | Type | Rules |
|-------|------|-------|
| received_at | timestamp | |
| metric | `LCP` / `INP` / `CLS` | |
| value | float | Metric value (not money) |
| route | text, ≤ 50 | Route name, for example `catalog:category`, never the full URL |
| device_class | `mobile` / `desktop` | |

No cookies, identifiers or IP addresses. Rows older than 90 days are deleted daily.
