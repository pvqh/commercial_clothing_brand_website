# Contract: Shopper Routes

**Feature**: [spec.md](../spec.md) | **Data model**: [data-model.md](../data-model.md)

Public, server-rendered HTML pages. Every page works without JavaScript. Russian is served at the
root, English under `/en/` (research R6). Shoppers get no cookies.

## Routes

| Name | Russian | English | Purpose |
|------|---------|---------|---------|
| `catalog:home` | `/` | `/en/` | Catalog landing: published categories in navigation order |
| `catalog:category` | `/katalog/<category-slug>/` | `/en/catalog/<category-slug>/` | Category listing (US1, US3) |
| `catalog:product` | `/tovar/<product-slug>/` | `/en/product/<product-slug>/` | Product page (US1, US2, US4) |
| `sitemap` | `/sitemap.xml` | — | Both languages, with `hreflang` alternates |
| `robots` | `/robots.txt` | — | Disallows `/staff/`; links the sitemap |
| `rum` | `POST /rum/` | — | Field Core Web Vitals beacon (research R12) |

Slugs follow research R7. Path words (`katalog`/`catalog`, `tovar`/`product`) are translated
interface strings.

## Category listing query parameters

| Param | Values | Default | Rule |
|-------|--------|---------|------|
| `size` | size code (`xxs` … `xxxl`, `one`), repeatable | none | Any of the chosen sizes in stock in at least one color (FR-007, FR-008) |
| `price_min` | whole rubles, integer ≥ 0 | none | Inclusive (US3-3) |
| `price_max` | whole rubles, integer ≥ 0 | none | Inclusive |
| `sort` | `new`, `price_asc`, `price_desc` | `new` | FR-012, FR-013 |
| `page` | integer ≥ 2 | 1 (omitted) | 24 products per page (FR-004) |

**Normalisation** (research R13): unknown sizes and non-numeric values are dropped; `price_min` >
`price_max` are swapped; sizes are sorted by the size scale and de-duplicated; default values are
omitted; parameters are written in the order above. If the normalised address differs from the
request, the response is **302** to the normalised address. A page beyond the last becomes the
last page (or no `page` when there is one page).

Only sizes that appear in the category's published products are offered as filter choices
(FR-006).

## Product page query parameters

| Param | Values | Rule |
|-------|--------|------|
| `color` | a Color id of this product | Selects the color; invalid → 302 to the address without it |

## Responses

| Situation | Status | Body |
|-----------|--------|------|
| Published category or product | 200 | Page |
| Sold-out product | 200 | Page with "Sold out"; JSON-LD availability `OutOfStock` |
| Published category with no published products | 200 | "No products yet" message; `noindex`; not in navigation |
| Old slug of a renamed product or category | 301 | → current slug, same language, same query |
| Non-normalised query | 302 | → normalised address |
| Unpublished or unknown product or category | 404 | "Not found" page with a link to `catalog:home` (FR-005) |
| HTMX request (`HX-Request: true`) | same as above | Same full HTML; HTMX selects the region it needs (research R3) |

## Listing page content

- Navigation with every category shown in navigation (data model, Category).
- Breadcrumbs, H1 with the category name, result count in an `aria-live="polite"` region.
- Filter bar: one form (`method="get"`) holding `<details>` dropdowns for Size (checkboxes) and
  Price (from/to inputs), a sort select, and a «Показать» / "Show" submit button. With HTMX the
  results update on change and the button stays as a fallback. Active filters are listed with one
  remove link each, plus "Clear all" (FR-010).
- Product cards: listing photo (`<picture>`, 2:3), name (ellipsis when long), price as
  `125 000 ₽` or `от 125 000 ₽` / `From 125 000 ₽` when matching variant prices differ, and a
  "Sold out" label when applicable (FR-003, FR-023).
- Empty result: "No products match" plus a "Clear all filters" link (FR-011).
- Pagination links (`rel="prev"`/`rel="next"`).

## Product page content

- Breadcrumbs from the primary category, and a "Back to <primary category>" link (FR-002).
- Gallery for the selected color, falling back to shared photos; every image has alt text. A
  horizontal scroll-snap strip on mobile and a two-column photo grid beside a sticky info panel from
  1024 px. No carousel script.
- Name, price (exact for the selected color and size, otherwise "From"), "Sold out" when no stock.
- Color options as links (`?color=<id>`) with `aria-current="true"` on the selected color and an
  "Out of stock" text label where the color has no stock (FR-021). Hidden for single-color
  products.
- Size options as a radio group. Out-of-stock sizes are shown, `disabled`, and labelled
  "Out of stock" in text (FR-020). Hidden for one-size products (FR-029).
- "Size guide" button opening a modal `<dialog>`: one table per size with body and garment
  measurements in cm and inches, plus how to measure. Closing returns focus to the button and keeps
  the selections (FR-026, FR-027). Without JavaScript, the guide is rendered in a `<details>`
  element on the page.
- Description, fur details (species, origin country, treatment), shell, lining and trim, care
  instructions (FR-015, FR-016), in `<details>` accordions under the info panel: Characteristics
  (fur and materials) open by default, then Description and Care.

Visual layout and components for both pages: [design-reference.md](../design-reference.md) §5–6.

## Head elements (every indexable page)

- `<html lang="ru">` or `lang="en"`.
- Unique `<title>` and `<meta name="description">`.
- `<link rel="canonical">`: the page itself without query parameters, except `page` ≥ 2 on
  listings.
- `<link rel="alternate" hreflang="ru|en|x-default">`, with `x-default` pointing to Russian.
- Open Graph: `og:title`, `og:description`, `og:url`, `og:image` (listing photo, 1080 px),
  `og:locale` (`ru_RU` / `en_US`).
- Any filtered, sorted or `color` view: `<meta name="robots" content="noindex, follow">`.

## Structured data (product page)

JSON-LD in `<script type="application/ld+json">`:

- `Product`: `name`, `description`, `image` (all gallery URLs), `sku` (product id), `brand`
  (placeholder until the brand name is confirmed), `material`.
- `offers`: one `Offer` when all variants share a price, otherwise `AggregateOffer` with
  `lowPrice`/`highPrice`; `priceCurrency: "RUB"`; `availability` `https://schema.org/InStock` if
  any variant has stock, else `https://schema.org/OutOfStock`; `url` = canonical.
- `BreadcrumbList`: catalog home → primary category → product.

## Caching

`Cache-Control: public, max-age=60` on 200 responses (FR-024). 404 and 3xx responses are not
cached. Photo renditions: `Cache-Control: public, max-age=31536000, immutable`.

## RUM beacon

`POST /rum/` with JSON `{"metric": "LCP"|"INP"|"CLS", "value": <number>, "route": "<route name>",
"device": "mobile"|"desktop"}`. Response **204**. Invalid body → **400**. No cookie and no CSRF
token (the endpoint changes nothing but an anonymous counter table). Rate-limited at Caddy.
