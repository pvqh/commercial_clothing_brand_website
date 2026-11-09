# Design Reference: mexa-ekaterina.ru

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Studied**: 2026-11-09

The brand asked us to use <https://mexa-ekaterina.ru/> ("Меха Екатерина", a Moscow fur retailer) as the
example for our design direction. This document records what that site does: its sections,
components, design values and images. It then states what we adopt, what we deliberately do
differently, and why.

**Method**: Live inspection in Chrome on desktop (1536 × 730 viewport): computed styles, DOM structure,
stylesheets, loaded fonts, structured data, Performance API and HEAD requests on every image. Pages
studied: home, category listing (`/collections/verkhnyaya_odezhda/shuby/`) and a product page
(`/collections/verkhnyaya_odezhda/shuba_iz_mekha_lisitsy_300633/`). The site's cookie banner was
hidden locally and never accepted. The mobile layout was read from the site's CSS media queries,
because the browser window could not be resized during the session.

> **Use as reference, not as source.** The reference's logo, monogram, photographs, copy and icons
> belong to Меха Екатерина. We take layout ideas, proportions and mood only. No asset is downloaded
> or reused (see [Image inventory](#image-inventory)). The accent color is our own brand's decision,
> because the two brands sell the same goods in the same market and a near-identical look invites
> confusion with a competitor.

---

## 1. Overall impression

- **Mood**: quiet luxury. Mostly white space, black text, one deep red accent, studio photos on a light
  grey background, uppercase labels, pill-shaped buttons, a large script "E" monogram as a watermark.
- **Type**: one sans-serif family (Manrope, variable 200–800) everywhere. Hierarchy comes from size and
  uppercase, not from bold weights (98% of text is 300 or 400).
- **Rhythm**: generous vertical spacing (150 px between home sections on desktop, 60 px on mobile),
  wide content (container up to 1890 px, 15 px side gutters).
- **Photography**: models photographed full length on a plain light grey studio background, portrait
  **2:3** (1000 × 1500 px). That is the most transferable lesson for long fur coats.

## 2. Detected sections and component breakdown

### 2.1 Global (every page)

| # | Section | What it contains | Measurements |
|---|---------|------------------|--------------|
| G1 | **Top bar** (fixed) | Left: phone, Telegram, WhatsApp icons. Centre: logo (SVG monogram + wordmark). Right: search, wishlist and cart (with count badges), account, language switch `EN`, hamburger in a round button | 90 px tall; logo 120 × 75; hamburger 50 × 50, background #FAFAFA, radius 50% |
| G2 | **Category bar** | `КАТАЛОГ ▾` (mega menu), Адреса и контакты, Доставка и возврат, `АТЕЛЬЕ ▾`, Химчистка, Хранение. Uppercase, spread across the full width | 51 px tall, white, 16 px text |
| G3 | **Full-screen menu** | Hamburger overlay: menu plus contacts | Full viewport, white |
| G4 | **Breadcrumbs** | `Главная / Верхняя одежда / Шубы` | Small grey text |
| G5 | **Subscribe strip** | Email field, button, **separate unticked consent checkbox** for personal data and marketing | 151 px |
| G6 | **Footer** | Logo, link columns (catalog, services, other), phone numbers, social icons, faint monogram watermark | Background #1C1C20, white text, padding 80 / 0 / 30 px |
| G7 | Floating widgets | Chat bubble (RetailCRM), cookie bar ("continuing means you accept"), callback modal | — |

### 2.2 Home page (top to bottom)

| # | Section | Content | Height (desktop) |
|---|---------|---------|------------------|
| H1 | Hero banner | Two editorial photos side by side, caption and an outlined "В каталог" pill | 590 px |
| H2 | Advantages | 5 cards in a 3-column grid: red line icon, uppercase title, grey one-line description (30 years, own production, convenience, guarantee, service) | 351 px |
| H3 | Product slider "Стильные шубы" | H2 on the left, outlined "В КАТАЛОГ →" pill on the right; 4 cards visible; round white arrow buttons (50 px) | 708 px |
| H4 | Services | Tall photo on the left; list on the right (uppercase title, grey paragraph, circular arrow link); giant monogram watermark | 623 px |
| H5 | Product slider "Меховые аксессуары" | Same as H3 | 705 px |
| H6 | Store addresses | Store list (flagship name in red, address, hours, "Показать отзывы") next to a carousel of store interiors | 780 px |
| H7 | About | Archive photo, long brand-history text, pull quote on a 4% red tint with rounded corners, second photo | 860 px |

### 2.3 Category listing

| Part | Detail |
|------|--------|
| H1 | «Шубы из натурального меха», 32 / 38.4 px, weight 400 |
| Sidebar | Nested catalog tree (Новинки, Верхняя одежда ▸ Шубы, Пальто…, Аксессуары ▸ …), expand/collapse chevrons |
| Filter bar | Horizontal row of dropdown triggers: Цена, Вид меха, Длина, Капюшон, Рисунок, Цвет, Размер. Each option shows a count («Норка 67»). A red **ПОКАЗАТЬ** (apply) button, a round reset button, and a sort select: По новинкам / По возрастанию цены / По убыванию цены / По популярности |
| Grid | 3 columns (about 347 px each), gap 50 px rows × 20 px columns, **24 products per page** |
| Pagination | Numbered links, `?PAGEN_1=2` |
| Sizes | **Russian numeric sizes 42–56**, not letters |
| URLs | Transliterated Latin slugs, nested: `/collections/verkhnyaya_odezhda/shuby/` |

### 2.4 Product card (listing and sliders)

| Element | Style |
|---------|-------|
| Image link | 2:3, radius 10 px, `object-fit: cover`, light grey studio background |
| Wishlist button | White circle with a heart, top right of the image |
| Title | 16 / 19.2 px, weight 400, **uppercase**, black, 8 px below the image |
| Price | 16 / 25.6 px, weight 300, accent red, «320 000 ₽» |
| Spacing | 30 px between image and title; card side margin 10 px |

### 2.5 Product page

| Part | Detail |
|------|--------|
| Gallery (left) | Vertical thumbnail column (188 × 283) plus main image (560 × 890), both 2:3; wishlist heart on the main image |
| Info panel (right) | Bordered panel with rounded corners: H1 32 px weight 400; small caps label «ЦЕНА»; price in red; «В НАЛИЧИИ:» with a store address link; size chips; «Подгонка» (fitting) note; «Поделиться» (share) |
| Size chip | 40 px tall, padding 0 14 px, 1 px black border, radius 5 px, background #FBFBFB |
| Primary button | «Добавить в корзину»: full width, red #A50408, white uppercase text, pill (radius 50 px), padding 22 × 23 px |
| Secondary button | «Консультация»: full width, outlined pill |
| Accordions | Характеристики изделия (fur type, color), Описание изделия (lining, length), Бесплатная подгонка, Доставка и возврат, Гарантия, Беспроцентная рассрочка |
| Identity | «Модель: 25003/0179 / Артикул: 300633»; the title includes the color: «Шуба из меха лисицы, цвет белый — купить в Москве \| Артикул: 300633» |
| Colors | **Each color is a separate product page** (no color selector) |
| Structured data | `Product` + `Offer` (RUB, InStock, NewCondition) + `aggregateRating`; separate `Organization` |
| Size guide | Not found on the product page |

## 3. Extracted design values

### 3.1 Colors (computed, by frequency)

| Role | Value | Where | Contrast on white |
|------|-------|-------|-------------------|
| Text | `#000000` | Headings, titles, nav | 21:1 |
| Accent | `#A50408` (rgb 165 4 8) | Prices, active nav, primary button, icons, links | 8.0:1 |
| Muted text | `#595959` | Paragraphs, descriptions | 7.0:1 |
| Faint text | `#777777` | Rare meta text | **4.48:1 (fails AA by a hair)** |
| Surface | `#FFFFFF` | Page | — |
| Subtle surface | `#FAFAFA` / `#FBFBFB` | Round icon buttons, size chips | — |
| Accent tint | `rgba(166, 12, 17, 0.04)` | Pull-quote background | — |
| Inverse surface | `#1C1C20` | Footer | White on it 17:1 |
| Borders | `#EFEFEF`, `#D0D0D0`, `#595959` | Cards, pills, inputs | #D0D0D0 is about 1.5:1, **too faint for form controls** (WCAG 1.4.11 needs 3:1) |

### 3.2 Typography

| Token | Value |
|-------|-------|
| Family | **Manrope** (variable, weights 200–800). Open source (SIL OFL), with Cyrillic |
| Body | 16 px; line heights 1.2 (titles), 1.4 (UI text), 1.6 (prose) |
| Weights | 400 (49%), **300 for body paragraphs** (44%), 500 for buttons and labels, 700 almost never |
| H1 / H2 | 32 / 38.4 px, weight 400. Mobile: H1 28 px, catalog H2 22 px |
| Uppercase | 43% of text elements: nav, card titles, buttons, labels |
| Letter spacing | Normal; 2 px on a few caps labels |

### 3.3 Spacing, shape, layout

| Token | Value |
|-------|-------|
| Container | max 1890 px, side padding 15 px |
| Section gap | 150 px desktop, 60 px mobile (≤ 767 px) |
| Grid gaps | 50 px rows, 20 px columns |
| Radii | 50% (round icon buttons), 10 px (cards, images), 5 px (size chips), 20–30 px (panels), 50 px (pills) |
| Control height | 50 px (buttons, round icons), 40 px (size chips) |
| Breakpoints | Desktop-first `max-width` queries, about 15 different values (1640, 1351, 1279, 1200, 1023, 992, 767, 756, 675, 599, 567, 420 …) |

### 3.4 Performance and privacy snapshot (product page, desktop, warm cache)

| Metric | Value |
|--------|-------|
| Requests | 89 |
| Images transferred | about 1.9 MB (20 images, one size each, **no `srcset`**, no lazy loading) |
| HTML | 57 KB; TTFB 0.6 s; LCP 0.9 s on desktop broadband |
| JS stack | jQuery 1.8.3, Slick carousel, Fancybox, Select2, Tooltipster, plus 1C-Bitrix core |
| Third parties | Yandex Metrica, Mindbox tracker and web push, Google reCAPTCHA, RetailCRM chat, programmatic ad DMP, unpkg CDN, Yandex Maps, **images from Amazon S3 eu-central-1** |

## 4. What we adopt, adapt or avoid

| Reference pattern | Decision | Reason |
|-------------------|----------|--------|
| White space, black text, one accent, uppercase labels, pill buttons | **Adopt** | Fits a premium fur brand; easy to express in tokens |
| Manrope as the only typeface | **Adopt** as the placeholder until the brand guide arrives | OFL licence, Cyrillic, variable font: one WOFF2 per subset fits the 100 KB font budget |
| Light weight (300) body text in grey | **Adapt**: body text at 400 | Thin grey Cyrillic text is hard to read on phones; accessibility first (Principle II) |
| 2:3 portrait product photos on a light grey studio background | **Adopt**: replaces our provisional 4:5 standard | Long coats (up to 145 cm) need the taller frame; listing and gallery use the same crop |
| 24 products per page, numbered pagination | **Adopt** (already FR-004) | Same as our spec |
| Transliterated Latin slugs | **Adopt** (already research R7) | Confirms common Russian practice |
| Filter bar of dropdowns with an apply button, sort select | **Adopt** as `<details>` dropdowns inside a GET form with a «Показать» submit | Works without JavaScript; matches FR-014 |
| Product card: image, uppercase title, accent price, radius 10 | **Adopt** without the wishlist heart | Wishlist is out of scope (spec Assumptions) |
| Info panel with accordions on the product page | **Adopt** with `<details>`/`<summary>` | Native, keyboard-accessible, no JS |
| Size chips | **Adopt** as a styled radio group; 44 px tall; out-of-stock chips crossed out **and** labelled in text | FR-020, WCAG target size |
| Primary pill button full width on mobile | **Adopt** for future cart button; size-guide trigger uses the secondary style | — |
| Dark footer #1C1C20 | **Adopt** | High contrast, premium |
| Nested category tree, sidebar | **Avoid**: flat category list in the top bar and a horizontal chip row on listings | Spec FR-001 (flat categories) |
| Each color as its own product | **Avoid** | Spec FR-018/FR-019: one product with color variants |
| Carousels (Slick + jQuery) | **Avoid**: CSS `scroll-snap` rows, no JS | JS budget, keyboard and screen-reader trouble with carousels |
| Thumbnail column + main image gallery | **Adapt**: mobile horizontal scroll-snap strip; desktop two-column photo grid beside a sticky info panel | No JS, no layout shift, all photos reachable by keyboard |
| Empty `alt` on product photos, no `srcset`, no lazy loading | **Avoid** | Principles I and II |
| "Continuing means you accept" cookie bar, trackers before consent, EU-hosted assets | **Avoid** | Principle VI (opt-in consent, data in Russia) |
| Faint `#777` text and `#D0D0D0` control borders | **Avoid**: muted text #595959, control borders #767676 | WCAG 1.4.3 and 1.4.11 |
| Desktop-first, about 15 breakpoints | **Avoid**: mobile-first with 3 breakpoints | Principle I |
| Script monogram watermark, red accent #A50408 | **Do not copy** | Their trademark look; our brand supplies its own logo and accent |
| Hero, advantages, services, store list, about, subscribe, chat | **Later** (roadmap step 5, Marketing extras) | Not part of the catalog feature |

## 5. Proposed design tokens (provisional)

These go into `static/css/tokens.css` (research R4). They follow the reference's structure, are
checked for WCAG 2.2 AA, and use a **placeholder accent** until the brand guide sets the real one
(constitution `TODO(BRAND_GUIDELINES)`).

### Color

| Token | Value | Use | Contrast |
|-------|-------|-----|----------|
| `--color-text` | `#111111` | Body and headings | 18.9:1 on white |
| `--color-text-muted` | `#595959` | Descriptions, meta, "Sold out" | 7.0:1 |
| `--color-text-inverse` | `#FFFFFF` | Footer, primary button text | 17:1 on `--color-surface-inverse` |
| `--color-text-inverse-muted` | `#B3B3B3` | Footer secondary text | 8.1:1 on inverse |
| `--color-surface` | `#FFFFFF` | Page | — |
| `--color-surface-subtle` | `#F7F7F7` | Chips, photo placeholders | — |
| `--color-surface-photo` | `#EEEEEE` | Behind product photos while loading | — |
| `--color-surface-inverse` | `#1C1C20` | Footer | — |
| `--color-border` | `#E6E6E6` | Decorative dividers and card outlines | (decorative) |
| `--color-border-control` | `#767676` | Inputs, chips, outlined buttons | 4.5:1 |
| `--color-accent` | `#7A4B2A` **placeholder** (warm brown) | Prices, active states, primary button | 7.3:1 |
| `--color-accent-tint` | `rgb(122 75 42 / 0.06)` | Highlight backgrounds | — |
| `--color-focus` | `#005FCC` | 2 px focus ring, 2 px offset | 6.0:1 |
| `--color-error` | `#B3261E` | Form errors | 6.6:1 |

### Typography

| Token | Value |
|-------|-------|
| `--font-family-base` | `"Manrope", system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif` |
| `--font-weight-regular` / `-medium` / `-light` | 400 / 500 / 300 (light only at ≥ 24 px) |
| `--font-size-xs` | 0.75rem (12 px): legal text only |
| `--font-size-sm` | 0.875rem (14 px): breadcrumbs, meta |
| `--font-size-md` | 1rem (16 px): body, card titles, buttons |
| `--font-size-lg` | 1.125rem (18 px): prices on the product page |
| `--font-size-xl` | clamp(1.375rem, 1.2rem + 0.8vw, 1.75rem): H2 (22 → 28 px) |
| `--font-size-2xl` | clamp(1.75rem, 1.5rem + 1vw, 2rem): H1 (28 → 32 px) |
| `--line-height-tight` / `-base` / `-prose` | 1.2 / 1.4 / 1.6 |
| `--letter-spacing-caps` | 0.04em (uppercase labels) |

### Spacing, shape, motion, layout

| Token | Value |
|-------|-------|
| `--space-1` … `--space-10` | 4, 8, 12, 16, 20, 24, 32, 48, 64, 96 px |
| `--space-section` | `--space-9` (64 px) mobile → 120 px from 1024 px |
| `--grid-gap-column` / `--grid-gap-row` | 12 px / 32 px mobile → 20 px / 48 px from 1024 px |
| `--container-max` | 1600 px |
| `--gutter` | 16 px mobile, 24 px from 600 px, 40 px from 1024 px |
| `--radius-sm` / `-md` / `-lg` / `-pill` | 4 px / 10 px / 20 px / 999px |
| `--control-height` | 48 px (buttons), 44 px (size chips): above the 24 px target minimum |
| `--duration-fast` / `--duration-base` | 150 ms / 250 ms, `ease-out`; set to 0 under `prefers-reduced-motion` |
| `--ratio-product-photo` | 2 / 3 |
| Breakpoints (mobile-first `min-width`) | 600 px (listing 3 columns), 1024 px (desktop layout: sticky product panel, 4-column listing), 1440 px (wider gutters) |

Listing grid: 2 columns at 360 px (each card about 158 px wide), 3 from 600 px, 4 from 1024 px.

## 6. Component map (reference → our component library)

Files under `templates/components/`, each with one CSS section in `static/css/site.css`
(research R5).

| Our component | Reference source | Notes |
|---------------|------------------|-------|
| `site_header.html` | G1 + G2 | Logo, flat category links, language switch. On mobile, categories move into a `<details>` menu. No wishlist, cart or account icons yet |
| `language_switch.html` | G1 `EN` | Text link to the same page in the other language (FR-035) |
| `breadcrumbs.html` | G4 | `<nav aria-label>` + `<ol>`; BreadcrumbList JSON-LD |
| `section_heading.html` | H3 heading + pill link | H1/H2 with an optional outlined pill link |
| `button.html` | Pill buttons | Variants: `primary`, `secondary` (outlined), `icon` (round) |
| `product_card.html` | 2.4 | `<picture>` 2:3, uppercase title (CSS only), price via `price.html`, "Sold out" label |
| `product_grid.html` | 2.3 grid | Responsive grid, 24 per page |
| `category_chips.html` | Replaces the sidebar tree | Horizontal scroll-snap row of flat categories |
| `filter_bar.html` | 2.3 filter bar | `<details>` dropdowns (Size, Price) + sort select + «Показать» submit + reset link, in one GET form |
| `active_filters.html` | — (missing in reference) | Removable chips and «Сбросить все» (FR-010) |
| `pagination.html` | 2.3 | Numbered links, `rel="prev"`/`"next"` |
| `empty_state.html` | — | "No products match" + clear filters (FR-011) |
| `product_gallery.html` | 2.5 gallery | Scroll-snap strip (mobile), 2-column grid (desktop), first image `fetchpriority="high"` |
| `color_options.html` | — (reference splits colors into products) | Links with `aria-current`, "Out of stock" text |
| `size_selector.html` | 2.5 size chips | Radio group; disabled + "Out of stock" text |
| `price.html` | Card and product price | `125 000 ₽`, «от» / "From" variant |
| `info_accordion.html` | 2.5 accordions | `<details>`: Characteristics (fur species, origin, treatment, materials), Description, Care |
| `size_guide_dialog.html` | — (not in reference) | `<dialog>` with cm/inch table; `<details>` fallback |
| `site_footer.html` | G6 | Dark footer with category links and language switch |
| `picture.html` | — | Shared `<picture>` with AVIF/WebP/JPEG `srcset`, width/height, lazy loading |
| `icon.html` | Line icons | Inline SVG `<use>` from one sprite |

## Image inventory

62 distinct image URLs were found on the home page and checked with an HTTP HEAD request on
2026-11-09. **No file was downloaded**: every asset is the reference brand's property. The "Our
fallback" column says what our site uses instead.

| Group | Count | Format, natural size | Weight each | HEAD status | Alt text | Our fallback |
|-------|------:|----------------------|-------------|-------------|----------|--------------|
| Logo (`/local/templates/mexa/img/logo.svg`, `logo.png`) | 2 | SVG; PNG 198 × 122 | < 5 KB | 200 | Empty on SVG | Our brand's logo (pending brand guide); text wordmark placeholder |
| Hero banners (`/upload/iblock/…/159A0030.webp`, `159A3236.webp`) | 2 | WebP 1400 × 870 | 25–39 KB | 200 | Empty | Out of scope (marketing); neutral placeholder block if needed |
| Advantage icons (`/upload/iblock/…/*.svg`) | 5 | SVG 27–150 px | < 1 KB | 200 | Empty | Lucide icons (ISC licence) in `static/icons/sprite.svg` |
| Product photos in sliders (`/upload/iblock/…/*.webp`) | 36 | WebP 1000 × 1500 (2:3) | 23–205 KB | 200 | **Empty** | Brand's own photos through the import (2:3, ≥ 1440 px wide); dev/test fixtures are generated grey 2:3 images with the product name drawn on them |
| Mega-menu promo (`/upload/resize_cache/…`) | 1 | JPEG 120 × 180 | 15 KB | 200 | Empty | Not used |
| Service photo (`/local/templates/mexa/new_170724/images/pic/service.jpg`) | 1 | JPEG 700 × 1052 | 101 KB | 200 | Empty | Out of scope |
| Store interiors (`/images/contacts/1–5.webp`) + store hero JPEG | 6 | WebP 500 × 333/750; JPEG 1400 × 870 | 24–333 KB | 200 | Empty | Out of scope |
| About section archive photos (`/upload/medialibrary/…jpg`) | 2 | JPEG 667 × 1024 | 301–435 KB | 200 | Empty | Out of scope |
| Subscribe background and success images | 3 | WebP/JPEG 339–500 px | 31–41 KB | 200 | Empty | Out of scope |
| Footer developer badge (`/upload/developer.png`) | 1 | PNG 53 × 38 | 3 KB | 200 | Empty | Not used |
| Chat widget images (RetailCRM, incl. Amazon S3 eu-central-1) | 3 | SVG/PNG | — | 1 × 200, **2 × failed to fetch** (cross-origin) | Partly | Not used (no third-party widgets) |
| Product page gallery (`/upload/iblock/…/159A00xx.webp`) | 4 unique (rendered 3× each) | WebP 1000 × 1500 | — | 200 | Thumbs empty; main «Шуба из меха лисицы», «…_1» | As product photos above |

**Findings**: all 59 first-party images are reachable (HTTP 200). 58 of 59 have empty alt text. None
uses `srcset` or `loading="lazy"`. One size is served to every screen. The heaviest page images are
JPEGs (333 KB and 435 KB) that the site also has as WebP.

**Our rules** (research R12): 2:3 photos, renditions at 360 / 720 / 1080 / 1440 px in AVIF, WebP and
JPEG, alt text required in Russian, `loading="lazy"` below the fold, explicit width and height, grey
`--color-surface-photo` behind each image while it loads.

## 7. Decisions for the brand

**Status (2026-11-09)**: all four are deferred to a later spec change and are not part of this
feature's tasks.

1. **Sizes**: the reference and the Russian fur market use numeric sizes (42–56). Our spec (FR-009,
   clarified 2026-11-08) uses letters XXS–XXXL. Staying with letters is fine for the build. If shoppers
   are expected to think in Russian sizes, the size guide should show the Russian equivalent of
   each letter (for example "M — 44–46"). That is a content change, not a model change. Switching
   the scale itself would need a spec revision.
2. **Fur-type filter**: the reference's most-used facet is fur type («Норка 67», «Лисица 16»). Our
   spec filters by size and price only. If categories are not per fur type, a fur-type filter is the
   strongest candidate for a later spec change.
3. **Article number**: the reference shows «Модель» and «Артикул» on every product, and staff and
   shoppers quote it by phone. Consider adding an article number to the product in a later spec
   change. It would replace the database id in JSON-LD `sku`.
4. **Accent color and logo**: needed from the brand guide. The placeholder brown is deliberately not
   the reference's red.
