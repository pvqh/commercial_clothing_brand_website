# Feature Specification: Product Catalog

**Feature Branch**: `001-product-catalog`

**Created**: 2026-11-08

**Status**: Draft

**Input**: User description: "Shoppers can browse the catalog by category (men, women, accessories),
filter by size, color and price, and sort by newest or price. Each product has multiple photos,
size/color variants with per-variant stock, a size guide, and shows "out of stock" for unavailable
sizes."

## Clarifications

### Session 2026-11-08

- Q: Do categories need subcategories? → A: The final categories are not known yet and will change
  later. The brand sells fur coats, so the structure must stay simple: a flat list of categories
  defined in the catalog data, with no subcategories. Men, Women and Accessories are examples only.
- Q: How does product data get into the catalog before the admin feature exists? → A: The launch
  catalog is loaded from a spreadsheet. How staff update the catalog after launch is settled by the
  staff-area clarification below.
- Q: Which language(s) and currency does the catalog use? → A: The brand is in Russia and is not
  selling internationally yet. Russian is the main language and English is secondary; shoppers can
  switch between them. Prices are shown in rubles in both languages; there are no US dollar prices.
- Q: Should shoppers be able to filter by color? → A: No. Color is chosen on the product page only.
- Q: Should all sized products use one shared size scale? → A: Yes: one letter scale (XXS–XXXL) in a
  fixed order, plus "One size"; no numeric or regional sizes at launch.
- Q: Which category does a product in several categories show in its breadcrumb? → A: Each product
  has one primary category (the first one listed for it), used for its breadcrumb and its "back to
  category" link.
- Q: How do staff update products without the admin's help? → A: Through a staff-only area of the
  website, part of this feature (a recorded change to the roadmap order). The admin is the developer
  and handles technical matters; staff are store employees who maintain the catalog. Every price,
  stock and publish change records who made it, when, and the old and new values, and can be undone.
- Q: What does the English version show when English text is missing? → A: The Russian text, and
  the staff area flags the product as missing a translation.
- Q: Which language do page addresses use? → A: All text, addresses included, follows the selected
  language: Russian addresses in the Russian version, English addresses in the English version.
- Q: Which privacy law applies? → A: Russian law (152-FZ), including storing personal data in
  Russia. The constitution is updated to match.
- Q: How do staff sign in? → A: With a username and password only; no second sign-in step.
- Q: Which basic protections apply to password sign-in? → A: A minimum password length, a temporary
  lock after repeated wrong passwords, and automatic sign-out after inactivity.
- Q: Do all staff have the same permissions? → A: Yes, one staff level with full catalog editing;
  the admin is the only other role.
- Q: Do staff changes need approval before going live? → A: No; they go live straight away.
- Q: What does the change history cover? → A: Every catalog edit, with who, when, and the old and
  new values, and any recorded change can be undone.
- Q: Is the spreadsheet import still needed? → A: Yes, as a one-time bulk load of the launch
  catalog run by the admin; there is no re-import.
- Q: How long is staff data kept? → A: The change history keeps staff names for 3 years, after
  which the names are removed; a departing staff member's account is disabled, not deleted.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse a category and open a product (Priority: P1)

A shopper picks a category (for example, Women's Coats) from the main navigation, scrolls through the
products in it, and opens one to see its photos, description and price.

**Why this priority**: Without browsing and a product page there is no catalog; every other story
builds on this one.

**Independent Test**: Import a set of published products into two categories, open each category
from the navigation and confirm the right products appear and each opens a product page with its
photos, name, description and price.

**Acceptance Scenarios**:

1. **Given** published products exist in a category, **When** the shopper selects that category in
   the navigation, **Then** a listing of its products appears, each showing its main photo, name and
   price, newest first.
2. **Given** a category has more than 24 products, **When** the shopper reaches the end of the first
   page, **Then** they can move to the next page, and each page has its own shareable address.
3. **Given** a listing is shown, **When** the shopper selects a product, **Then** its product page
   opens showing all of its photos, name, description, fur and material details, care instructions
   and price.
4. **Given** a product is unpublished, **When** anyone opens its address, **Then** a "not found"
   page is shown with a link back to the catalog.

---

### User Story 2 - Choose a size and color and see availability (Priority: P1)

On a product page the shopper picks a color, sees the photos for that color, and picks a size.
Sizes that are not in stock in that color are clearly marked "Out of stock" and cannot be selected.

**Why this priority**: Shoppers abandon a store that lets them choose a size that cannot be bought;
accurate per-variant availability is the core promise of this feature.

**Independent Test**: Set up a coat with three colors and five sizes where some combinations have
zero stock, then confirm on the product page that each combination's status matches the stock data.

**Acceptance Scenarios**:

1. **Given** a coat in Black and Natural, **When** the shopper selects Natural, **Then** the gallery
   switches to the Natural photos and the size options show availability for Natural.
2. **Given** size M in Natural has zero stock, **When** Natural is selected, **Then** M is still
   visible, is labelled "Out of stock" in text, and cannot be selected.
3. **Given** every size of a color has zero stock, **When** the shopper views the color options,
   **Then** that color is labelled "Out of stock".
4. **Given** every variant of a product has zero stock, **When** the shopper opens the product page,
   **Then** the page still loads and shows "Sold out", and the listing shows a "Sold out" label.
5. **Given** sizes of a product have different prices, **When** the shopper views the listing,
   **Then** it shows "From" followed by the lowest price, and the product page shows the exact price
   once a size and color are selected.

---

### User Story 3 - Filter and sort a category (Priority: P2)

A shopper narrows a category to their size and a price range, then sorts the results by newest or
by price.

**Why this priority**: Filtering turns a long listing into a short, relevant one and is the main way
shoppers find something in their size, but the catalog is still usable without it.

**Independent Test**: With a known set of products, apply each filter and sort option alone and in
combination and confirm the results and their order match the expected set.

**Acceptance Scenarios**:

1. **Given** the shopper is viewing a category, **When** they filter by size L, **Then** only
   products with size L in stock (in at least one color) are shown, with the result count updated.
2. **Given** the shopper selects sizes M and L, **When** results update, **Then** products with M or
   L in stock are shown.
3. **Given** the shopper sets a price range, **When** results update, **Then** only products with an
   in-stock variant priced within the range (inclusive) are shown.
4. **Given** the shopper filters by size L and a price range, **When** results update, **Then** only
   products with an in-stock size L variant priced within the range are shown.
5. **Given** filters are active, **When** the shopper sorts by "Price: low to high", **Then** the
   filtered results are ordered by their lowest in-stock price, ascending.
6. **Given** filters are active, **When** the shopper copies the page address and opens it in a new
   browser, **Then** the same filters, sort order and results appear.
7. **Given** a filter combination matches nothing, **When** results update, **Then** a message says
   no products match and offers to clear all filters.

---

### User Story 4 - Check the size guide (Priority: P3)

Before choosing a size, the shopper opens the size guide from the product page to compare their
measurements with the brand's sizes, then closes it and continues where they were.

**Why this priority**: Fur coats are costly to return, so the size guide reduces wrong-size
purchases, but shoppers can still browse and pick sizes without it.

**Independent Test**: Open the size guide from a coat's product page, check the measurements shown
match that product's guide, close it and confirm the shopper's color and size choices are unchanged.

**Acceptance Scenarios**:

1. **Given** a coat's product page, **When** the shopper selects "Size guide", **Then** the guide
   opens without leaving the page and shows each size's measurements in centimetres and inches, plus
   how to measure.
2. **Given** the size guide is open, **When** the shopper closes it, **Then** they return to the same
   place on the product page with their selections kept.
3. **Given** an item that comes in one size only (for example, a fur scarf), **When** the shopper
   opens its page, **Then** no size selector or size guide is shown.

---

### User Story 5 - Load the launch catalog from a spreadsheet (Priority: P1)

Before launch, staff fill in a spreadsheet with the categories, products, variants, stock, prices,
photo references and size guides, and the admin loads the catalog from it once.

**Why this priority**: Typing a whole launch catalog of hundreds of products and thousands of
variants into the staff area one by one is slow and error-prone; a bulk load fills the shop at once.

**Independent Test**: Import a sample spreadsheet with valid and invalid rows and confirm the valid
products appear in the catalog exactly as described and every invalid row is reported.

**Acceptance Scenarios**:

1. **Given** a completed spreadsheet, **When** it is imported, **Then** every category, product,
   variant, stock quantity, price, photo and size guide in it appears in the catalog.
2. **Given** a spreadsheet row is missing a required value or refers to a missing photo, **When** it
   is imported, **Then** that product is not published and the import report lists the row number
   and the problem.
3. **Given** a spreadsheet names a category that does not exist yet, **When** it is imported,
   **Then** the category is created and appears in the navigation.

---

### User Story 6 - Staff keep the catalog up to date (Priority: P1)

A staff member signs in to the staff area, adds a new coat with its photos, sizes, colors, stock,
prices and texts in Russian and English, changes the price of another, and unpublishes a third,
all without asking the admin. Later the admin or another staff member checks the change history to
see who changed what, and undoes a mistaken price change.

**Why this priority**: The brand cannot keep its catalog current after launch without it, and the
admin should handle only technical work, not day-to-day product updates.

**Independent Test**: Create a staff account, sign in, make one change of each kind (price, stock,
publish status, text, photo) and confirm each appears on the shop and that every change is listed
in the change history with who, when, and old and new values.

**Acceptance Scenarios**:

1. **Given** a person without a staff account, **When** they try to open the staff area, **Then**
   they are refused and see no catalog data.
2. **Given** a signed-in staff member, **When** they change a variant's price, **Then** the new price
   is shown to shoppers within 5 minutes, and the change history records the staff member, the time,
   and the old and new price.
3. **Given** a mistaken price change in the change history, **When** a staff member undoes it,
   **Then** the old price is restored and the undo is itself recorded in the change history.
4. **Given** a product with Russian text only, **When** staff view the product list in the staff
   area, **Then** the product is flagged as missing English text.
5. **Given** a staff member unpublishes a product, **When** a shopper opens its address, **Then** a
   "not found" page is shown, and the change history records who unpublished it and when.
6. **Given** a staff member deletes a photo or edits a description, **When** anyone opens the change
   history, **Then** the edit is listed with who, when, and the old and new content, and can be
   undone.
7. **Given** the admin disables a staff account, **When** that person tries to sign in, **Then**
   they are refused, and their past changes stay in the change history under their name.
8. **Given** someone enters a wrong password for a staff account 5 times in a row, **When** they
   try again, **Then** the account is locked for 15 minutes, even with the right password.

---

### Edge Cases

- A product has only one photo, or a color has no photos of its own: the product's main photos are
  shown instead.
- A product comes in a single color: no color selector is shown.
- A category has no published products: it is hidden from the navigation.
- Stock changes while the shopper is on the page: the new status appears on the next page load;
  the final stock check at purchase belongs to the cart and checkout feature.
- The shopper enters a minimum price higher than the maximum: the values are swapped.
- A page address contains unknown filter values or a page number beyond the last page: unknown
  values are ignored and the shopper is taken to the last valid page.
- A category is renamed: its old address redirects to the new one.
- A product is in more than one category: it appears in each listing and has one product page,
  whose breadcrumb always shows its primary category.
- A product name or description is very long: it wraps on the product page and is shortened with an
  ellipsis in listings.

## Requirements *(mandatory)*

### Functional Requirements

**Categories and listings**

- **FR-001**: Categories MUST be a single flat list (no subcategories) defined in the catalog data,
  so categories can be added, renamed or removed without changing the website. Every category with
  published products MUST be reachable from the main navigation on every page.
- **FR-002**: A product MUST be able to belong to more than one category. One of them, the first
  listed for the product, MUST be its primary category, used for its breadcrumb and its "back to
  category" link whichever listing the shopper came from.
- **FR-003**: Category listings MUST show each product's main photo, name, price and, when no variant
  is in stock, a "Sold out" label.
- **FR-004**: Listings MUST show 24 products per page, and each page MUST have its own address.
- **FR-005**: Only published products MUST appear in listings; an unpublished product's address MUST
  show a "not found" page.

**Filtering and sorting**

- **FR-006**: Shoppers MUST be able to filter a category by size and price range. The size choices
  offered MUST come from the products in that category. There is no color filter.
- **FR-007**: Several sizes chosen together MUST match products with any of them; the size filter
  and the price range MUST apply together.
- **FR-008**: The size filter MUST match only sizes that are in stock in at least one color.
- **FR-009**: All sized products MUST use one shared size scale, XXS, XS, S, M, L, XL, XXL, XXXL, in
  that order; products without sizes use "One size". Numeric and regional sizes are not offered.
- **FR-010**: Listings MUST show the number of results and each active filter, and let shoppers
  remove filters one at a time or all at once.
- **FR-011**: When no products match, listings MUST say so and offer to clear all filters.
- **FR-012**: Shoppers MUST be able to sort by Newest (the default, by date first published),
  Price: low to high, and Price: high to low.
- **FR-013**: Price filtering and sorting MUST use the product's lowest in-stock variant price.
- **FR-014**: The active filters, sort order and page MUST be part of the page address so the view
  can be shared, bookmarked, and restored with the browser's back and forward buttons.

**Product page**

- **FR-015**: Product pages MUST show the product's name, description, care instructions, price, a
  photo gallery, and its color and size options.
- **FR-016**: Product pages MUST show the product's fur details: the fur type (animal species), the
  country of origin, and whether the fur is dyed or otherwise treated, plus the materials of the
  shell, lining and trim.
- **FR-017**: Each product MUST have at least one photo, and every photo MUST have a text description
  for shoppers who cannot see it.
- **FR-018**: Selecting a color MUST show that color's photos and that color's size availability.
- **FR-019**: Each size/color combination (variant) MUST have its own stock quantity and price.
- **FR-020**: Sizes with no stock in the selected color MUST stay visible, be labelled "Out of stock"
  in text, and not be selectable.
- **FR-021**: A color with no stock in any size MUST be labelled "Out of stock".
- **FR-022**: A product with no stock in any variant MUST keep its page available and show
  "Sold out".
- **FR-023**: When variant prices differ, listings MUST show "From" and the lowest price, and the
  product page MUST show the exact price of the selected variant.
- **FR-024**: What shoppers see MUST reflect any stock, price or publish change within 5 minutes.
- **FR-025**: Each product and category MUST have a stable, readable address in each language, based
  on its name in that language: Russian in the Russian version, English in the English version
  (the Russian name when the English one is missing). Switching language MUST open the same page at
  its address in the other language. A renamed product or category MUST redirect from its old
  address.

**Size guide**

- **FR-026**: Product pages for sized items MUST offer a size guide that opens without leaving the
  page and keeps the shopper's selections when closed.
- **FR-027**: A size guide MUST show, for each size, body measurements (chest, waist, hips) and
  garment measurements (sleeve and coat length) in centimetres and inches, plus instructions on how
  to measure.
- **FR-028**: Size guides MUST be set per product type (e.g., women's long coats); a product MAY have
  its own guide that replaces the product type's guide.
- **FR-029**: Products with a single size MUST NOT show a size selector or size guide.

**Launch catalog import**

- **FR-030**: The admin MUST be able to load the launch catalog (categories, products, fur details,
  variants, stock, prices, photo references and size guides, with texts in Russian and English)
  once from a spreadsheet in a documented format.
- **FR-031**: The import MUST check every row. A product with a missing required value or a missing
  photo MUST NOT be published, and the import MUST report each problem with its row number.
- **FR-032**: After launch, staff maintain the catalog through the staff area (FR-038 to FR-044),
  not through re-imports.

**Access and privacy**

- **FR-033**: Browsing, filtering, sorting, the gallery, variant selection and the size guide MUST
  all work with a keyboard alone and with a screen reader; the selected state and the out-of-stock
  state MUST be conveyed in text, not by color alone.
- **FR-034**: The catalog MUST NOT collect personal data from shoppers, and MUST NOT load
  non-essential tracking before the shopper has consented. The only personal data this feature
  handles is staff account data (name, username, password) and staff names in the change history,
  used for staff sign-in and to trace changes, on the basis of the staff member's employment, and
  stored in Russia (constitution Principle VI).

**Language and currency**

- **FR-035**: The catalog MUST be available in Russian (the default) and English, and shoppers MUST
  be able to switch language from any page and stay on the same page. All shopper-facing text,
  including product content and page addresses, MUST follow the selected language.
- **FR-036**: When a product's English text for a field is missing, the English version MUST show
  its Russian text.
- **FR-037**: Prices MUST be shown in rubles in both languages.

**Staff catalog editing**

- **FR-038**: Staff MUST be able to create, edit, publish and unpublish categories, products,
  variants, stock, prices, photos and size guides, in Russian and English, in a staff-only area
  without the admin's help. All staff have the same permissions, and their changes go live without
  approval.
- **FR-039**: Only people with a staff account created by the admin MUST be able to enter the staff
  area, signing in with a username and password; everyone else MUST be refused and see no catalog
  data that is not public. The admin MUST be able to disable a staff account; a disabled account
  cannot sign in.
- **FR-040**: Staff passwords MUST be at least 12 characters long. After 5 wrong passwords in a row,
  the account MUST be locked for 15 minutes. A staff session MUST end after 2 hours without
  activity.
- **FR-041**: Every catalog change made in the staff area MUST be recorded in a change history with
  who made it, when, and the old and new values. Staff MUST NOT be able to edit or delete change
  history entries.
- **FR-042**: Staff MUST be able to undo a recorded change; the undo restores the old value and is
  itself recorded in the change history.
- **FR-043**: The staff area MUST flag every product that is missing English text.
- **FR-044**: Change history entries MUST keep the staff member's name for 3 years, after which the
  name MUST be removed from the entry. A departing staff member's account MUST be disabled, not
  deleted, so their earlier changes stay traceable.
- **FR-045**: Orders, stock movements, Chestny ZNAK marking and order handling by staff are out of
  scope; they belong to the "Admin and inventory" roadmap feature.

### Key Entities

- **Category**: A group of products shoppers browse (for example, Women's Coats). Has a name, a
  display order and a readable address per language; contains many products. Categories are not
  nested.
- **Product**: Something the brand sells, such as a style of coat. Has a name, description, fur
  details (fur type, country of origin, dyed or treated), shell, lining and trim materials, care
  instructions, publish status, date first published, product type and a readable address per
  language. Its shopper-facing text exists in Russian and, optionally, English. Belongs to one or
  more categories, one of which is its primary category, and has photos and variants.
- **Variant**: One buyable version of a product: a single size in a single color. Has its own stock
  quantity and price.
- **Color**: A named color option of a product (e.g., Natural, Black), with the photos that show it.
- **Size**: One step of the shared scale XXS, XS, S, M, L, XL, XXL, XXXL (in that order), or
  "One size".
- **Product Photo**: An image of a product, optionally tied to one color, with an order and a text
  description.
- **Size Guide**: A table of body and garment measurements per size, in centimetres and inches, with
  how-to-measure instructions. Belongs to a product type, or to a single product as an override.
- **Catalog Import**: One spreadsheet load, with the time it ran and a report of rows loaded and rows
  rejected with their problems.
- **Staff Member**: A store employee with a staff account created by the admin, who maintains the
  catalog in the staff area.
- **Change Record**: One entry in the change history: which catalog item changed, which value, the
  old and new values, who made the change and when. Entries cannot be edited or deleted; an undo
  adds a new entry. The staff name is removed after 3 years.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In usability testing, 90% of shoppers can go from any page to a list of products
  available in their size and price range in under 30 seconds.
- **SC-002**: On mobile phones, for at least 75% of visits, the main content of listing and product
  pages appears within 2.5 seconds, responds to taps within 0.2 seconds, and does not jump around
  while loading.
- **SC-003**: In stock audits, no size shown as available is actually out of stock more than 5
  minutes after a stock change.
- **SC-004**: 100% of published product pages and category pages can be found by search engines,
  and 100% of shared filtered addresses reproduce the same results when opened.
- **SC-005**: In usability testing, 90% of shoppers can find the size guide and pick their size
  without help.
- **SC-006**: Every catalog page passes a WCAG 2.2 AA accessibility audit with no serious or critical
  issues.
- **SC-007**: Applying or removing a filter shows updated results within 1 second for 95% of
  attempts.
- **SC-008**: The admin can load a launch catalog of 200 products from a staff-filled spreadsheet in
  under 15 minutes, and every rejected row is reported with a reason staff can act on.
- **SC-009**: A staff member can change a price, stock quantity or publish status and see it on the
  shop within 5 minutes without the admin's help, and 100% of staff changes appear in the change
  history with who, when, and the old and new values.

## Assumptions

- The product is a responsive website used in web browsers; native mobile apps are out of scope.
- The brand mainly sells fur coats, plus a small range of one-size accessories (e.g., scarves,
  hats); the final category names will be supplied by the brand.
- The brand name is not yet confirmed and is being verified with stakeholders; it does not affect
  this feature's requirements.
- The brand is based in Russia and sells only to the Russian market for now. Fur labelling wording
  (species, origin and treatment) follows Russian rules, which the brand confirms before launch.
  Mandatory fur marking in the Chestny ZNAK system (Data Matrix codes since 1 March 2026) applies
  when an item is sold, so it belongs to cart and checkout and to inventory, not to this feature.
- Russian consumer-protection law (Article 10.1, in force since 1 March 2026) requires public
  consumer information to be in Russian. Other languages are allowed only as an equivalent duplicate,
  so the English version mirrors the Russian content.
- Roadmap deviation: staff catalog editing is moved forward from the "Admin and inventory" feature
  (roadmap step 4) into this feature, because the catalog cannot be kept current after launch
  without it. Orders, stock movements and Chestny ZNAK marking stay in step 4.
- Handoff to the cart and checkout feature, so a staff mistake or misuse cannot turn into a cheap
  sale (constitution Principle V): an order always uses the price stored on the server, never a
  price sent by the browser, and orders placed shortly after a price change of their items are
  flagged so staff confirm them before shipping.
- The admin is the developer and handles technical work; staff are store employees and handle
  catalog content.
- Adding to cart, wishlists, search, reviews and "notify me when back in stock" belong to later
  features and are out of scope here.
- Prices are set in rubles, shown in rubles in both languages, and include any taxes that apply in
  Russia.
- The catalog will hold up to about 1,000 products and 20,000 variants in its first year.
- Only staff change catalog content; shoppers do not need to sign in to browse.
- Size guides are written and supplied by the brand.
- Product photography follows the brand's photo standard for aspect ratio and background
  (constitution Principle VII). Until the brand confirms otherwise, the standard is a full-length
  portrait photo (2:3) on a plain light background, the same crop in listings and on product pages.
- The visual design takes mexa-ekaterina.ru, chosen by the brand, as its example for layout and mood
  (see the plan's design reference). Its logo, photos, texts and colors are another company's
  property and are not reused. Where the example conflicts with the constitution (accessibility,
  speed, privacy), the constitution wins.
