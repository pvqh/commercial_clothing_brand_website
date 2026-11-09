# Glossary

The domain language of the catalog. Code, specs and reviews use these words with these meanings.
Rules live in `specs/001-product-catalog/data-model.md`; this file only fixes the names.

## Catalog

| Term | Meaning | In code |
|------|---------|---------|
| **Category** | A shelf of the catalog, such as "Шубы". Shown to shoppers only when it is published *and* holds at least one published product. | `Category` |
| **Shopper-visible category** | A published category that has a published product. The header, the footer, the home page and the sitemap list only these. | today: a filter repeated in 3 places, see `docs/architecture-review.md` §3.2 |
| **Product** | One model of garment or accessory, in both languages. | `Product` |
| **Primary category** | The category at position 0 of a product's memberships. Breadcrumbs and the admin list use it. | `Product.primary_category` |
| **Product type** | A kind of product, such as a coat or a scarf. It supplies the default size guide. | `ProductType` |
| **Color** | One colour of a product. It owns the product's variants and can own photos. | `Color` |
| **Variant** | One buyable size in one colour, with its own price and stock. | `Variant` |
| **Size** | A letter size from `xxs` to `xxxl`, or **one size**. A product never mixes the two. | `Size`, `Size.ONE` |
| **In stock** | A variant with stock above zero. | `stock__gt=0` |
| **Sold out** | A product, or a colour, with no variant in stock. | today: 6 implementations, see review §3.1 |
| **Card price** | The price shown on a listing card: the lowest in-stock price, or the lowest price of all variants when the product is sold out. It shows "from" when prices differ. | `card_price`, `card_price_is_from` |
| **Price range** | The same rule as the card price, applied on the product page, for one colour or for the whole product. | `PriceRange` |
| **Size guide** | Measurements per size, shown in cm and inches. | `SizeGuide`, `SizeGuideRow` |
| **Effective size guide** | The product's own size guide override, or else its product type's guide. | `Product.effective_size_guide` |
| **Photo** | An uploaded original. It is shared by every colour unless it is tied to one. | `ProductPhoto` |
| **Rendition** | A 2:3 copy of a photo at a fixed width (360, 720, 1080 or 1440) in AVIF, WebP or JPEG. Renditions are files, never rows. | `photos/<id>/<width>.<ext>` |

## Publishing and addresses

| Term | Meaning | In code |
|------|---------|---------|
| **Published** | Visible to shoppers. Products and categories are unpublished, never deleted. | `is_published` |
| **Publish rules** | The five checks a product must pass before it can be published. | `catalog/services/publishing.py` |
| **Draft** | An unpublished product, for example one the import saved with problems. | `is_published=False` |
| **Slug** | The readable Latin part of an address, one per language. | `slug_ru`, `slug_en` |
| **Slug redirect** | An old slug that answers with a 301 to the current address. | `CategorySlugRedirect`, `ProductSlugRedirect` |
| **Listing filters** | Size, price and sort chosen on a category page. | `ListingFilters` |
| **Normalised address** | The one canonical query string for a set of listing filters. Any other spelling of the same filters redirects to it with a 302. | `ListingFilters.query_string` |

## Staff area

| Term | Meaning | In code |
|------|---------|---------|
| **Staff area** | The Django admin at `/staff/`. It is always in Russian and never indexed. | `StaffAreaMiddleware` |
| **Catalog staff** | The group whose members edit the catalog but cannot manage accounts. | `catalog/staff_group.py` |
| **Change record** | One append-only line of history: a create, a delete, or a single changed field. | `ChangeRecord` |
| **Change set** | All change records written by one staff request. They are shown together. | `change_set` |
| **Undo** | Reverses one change record and writes new records that point back at it. | `audit/undo.py` |

## Launch import

| Term | Meaning | In code |
|------|---------|---------|
| **Launch import** | The one-time load of the starting catalog from a workbook and a folder of photos. It is refused after the first completed run. | `CatalogImporter` |
| **Workbook** | The `.xlsx` file with eight sheets, as described in `catalog_import/WORKBOOK_FORMAT.md`. | `read_workbook` |
| **Problem** | One bad value, identified by sheet, row and column. A problem either rejects its row or turns its product into a draft. | `ImportProblem` |

## Field metrics

| Term | Meaning | In code |
|------|---------|---------|
| **RUM sample** | One anonymous page-speed measurement (LCP, INP or CLS) sent by a shopper's browser. | `RumSample` |
