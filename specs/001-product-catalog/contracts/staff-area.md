# Contract: Staff Area

**Feature**: [spec.md](../spec.md) | **Data model**: [data-model.md](../data-model.md) |
**Research**: R8–R10

A customised Django admin at `/staff/`, in Russian. Not indexed (`robots.txt` disallow and
`X-Robots-Tag: noindex`).

## Roles

| Role | Who | Can |
|------|-----|-----|
| Admin | Django superuser (the developer) | Everything staff can, plus create staff accounts, disable and re-enable them, reset passwords, run the import (command line) |
| Staff | Active `is_staff` user in group "Catalog staff" | Create, edit, publish and unpublish all catalog records; view the change history; undo changes |
| Anyone else | | Only the sign-in page |

## Sign-in and session rules

| Rule | Behaviour | Spec |
|------|-----------|------|
| Not signed in | Any `/staff/` URL redirects to `/staff/login/`; no catalog data in the response | FR-039, US6-1 |
| Disabled account | Sign-in refused with the same message as a wrong password | FR-039, US6-7 |
| 5 wrong passwords in a row for one username | Username locked for 15 minutes; correct password refused during the lock | FR-040, US6-8 |
| Successful sign-in | Failed-attempt counter for that username reset | R10 |
| 2 hours with no request | Session ends; next request goes to sign-in | FR-040 |
| Password set or changed | At least 12 characters, not a common password | FR-040 |

## Screens

| Screen | Content and actions |
|--------|---------------------|
| Categories | List (name RU/EN, position, published, product count). Create, edit, publish/unpublish. No delete while products remain |
| Products | List with filters (published, category, product type, **Missing English**, sold out). Edit page groups the fields as Texts (RU \| EN side by side), Fur and materials, Categories (ordered inline; first = primary), Colors (inline), Variants (inline grid: color × size, price in rubles, stock), Photos (inline: upload, color, order, alt RU/EN), Size guide override. Actions: Publish selected, Unpublish selected. No delete |
| Product types | Name RU/EN, default size guide |
| Size guides | How to measure RU/EN; rows inline (size + five measurements in cm) |
| Change history | Read-only list: time, staff name (or "—" after 3 years), item, field, old → new, link to the item. Filters: item type, staff member, date. Per-record **Undo** button. Records from one save are grouped |
| Staff accounts (admin only) | Create, set name/username/password, disable/enable. No delete |

## Change history contract

- Every create, field change and delete on the screens above produces records as defined in
  [data-model.md](../data-model.md#changerecord-append-only), in the same transaction as the
  change. If recording fails, the change is rolled back.
- **Undo**: a POST with CSRF token from the change-history screen. Success shows "Change undone"
  and the new undo records. When refused (data model, Undo rules), nothing changes and the reason is
  shown in Russian.
- Nobody, including the admin, can edit or delete records through any screen. The database trigger
  enforces this for every other path.

## Publishing contract

Publishing (single or bulk) checks the Product publish rules in the data model. Products that fail
stay unpublished, and each failure is listed by product and rule. Others are published. Changes are
visible to shoppers on the next page load after `max-age` (≤ 60 s; FR-024, SC-009).

## Accessibility and look

- All staff screens pass the same axe checks as shopper pages (Principle II).
- The admin theme reads colors, fonts and radii from `tokens.css` (research R4, R8).
