# Contract: Launch Catalog Import

**Feature**: [spec.md](../spec.md) (User Story 5, FR-030–FR-032) |
**Data model**: [data-model.md](../data-model.md) | **Research**: R14

## Command

```text
uv run python manage.py import_catalog <workbook.xlsx> --photos <folder> [--dry-run] --run-by <admin username>
```

| Option | Meaning |
|--------|---------|
| `<workbook.xlsx>` | The staff-filled workbook described below |
| `--photos` | Folder containing every file named in the Photos sheet |
| `--dry-run` | Check everything and print the report; write nothing |
| `--run-by` | Username of the admin running the import (recorded on CatalogImport) |

**Exit codes**: `0` when the import (or dry run) completed, even if rows were rejected; `1` when it
could not run (file unreadable, a sheet or column missing, or a completed import already exists).

**Output**: a summary (products published, products saved as drafts, rows rejected) on the
console, and the full report as `<workbook>-report.csv` (columns: sheet, row, column, problem).
Problems are written in Russian so staff can act on them (SC-008).

## Workbook format

One sheet per table. Row 1 holds the exact column names below; data starts on row 2. Blank rows
are skipped. `*` marks a required column. `_ru` text is required wherever the matching field is
required in the data model; `_en` text is always optional. **Keys** are short labels invented by
staff (letters, digits, `-`) used only to link rows across sheets.

### Categories

| Column | Notes |
|--------|-------|
| category_key* | Unique |
| name_ru*, name_en | |
| position* | Integer ≥ 0 |

### SizeGuides

| Column | Notes |
|--------|-------|
| guide_key* | Unique |
| internal_name* | |
| how_to_measure_ru*, how_to_measure_en | |

### SizeGuideRows

| Column | Notes |
|--------|-------|
| guide_key* | Must exist in SizeGuides |
| size* | `xxs` … `xxxl` |
| chest_cm*, waist_cm*, hips_cm*, sleeve_cm*, length_cm* | Number > 0, one decimal place |

### ProductTypes

| Column | Notes |
|--------|-------|
| type_key* | Unique |
| name_ru*, name_en | |
| guide_key | Must exist in SizeGuides if given |

### Products

| Column | Notes |
|--------|-------|
| product_key* | Unique |
| name_ru*, name_en; description_ru*, description_en; care_ru*, care_en | |
| fur_species_ru*, fur_species_en; fur_origin_ru*, fur_origin_en | |
| fur_treatment* | `natural`, `dyed` or `treated` |
| fur_treatment_detail_ru, fur_treatment_detail_en | `_ru` required when `treated` |
| shell_ru*, shell_en; lining_ru*, lining_en; trim_ru, trim_en | |
| type_key* | Must exist in ProductTypes |
| guide_key | Override; must exist in SizeGuides if given |
| categories* | Comma-separated category keys; the **first is the primary category** |
| publish* | `yes` or `no` |

### Colors

| Column | Notes |
|--------|-------|
| product_key*, color_key* | color_key unique within its product |
| name_ru*, name_en | |
| position* | Integer ≥ 0, unique within the product |

### Variants

| Column | Notes |
|--------|-------|
| product_key*, color_key* | Must exist in Colors |
| size* | `xxs` … `xxxl` or `one`; unique per color; a product cannot mix `one` with letter sizes |
| price_rub* | Whole rubles, integer > 0 |
| stock* | Integer ≥ 0 |

### Photos

| Column | Notes |
|--------|-------|
| product_key* | |
| color_key | Empty = shared photo |
| file* | File name inside `--photos`; JPEG, PNG or WebP |
| position* | Integer ≥ 0; the lowest is the listing photo |
| alt_ru*, alt_en | |

## Validation and outcome

| Problem | Outcome |
|---------|---------|
| Missing sheet or column | Command exits `1` before importing anything |
| Completed import already exists | Command exits `1` (FR-032) |
| Invalid or missing required value in a Products row (no `product_key` or `name_ru`) | Row rejected; product skipped |
| Any other problem in a product's own rows (Products, Colors, Variants, Photos), including a missing photo file | Row rejected; product saved as an **unpublished draft** with the rest of its valid data (FR-031, US5-2) |
| Product with `publish = yes` that fails the publish rules | Saved as a draft; the failed rules are reported |
| Category key in `categories` not in Categories | Row rejected (staff add the category to the Categories sheet; US5-3 is met by listing every category there) |
| Problem in Categories, SizeGuides, SizeGuideRows or ProductTypes | Row rejected; products that depend on it are saved as drafts and the dependency is reported |

Categories with at least one imported product are published. Everything runs in one database
transaction: an unexpected error rolls back the whole import and marks it `failed`. Photo
renditions are generated in parallel processes before the transaction commits (research R12).
