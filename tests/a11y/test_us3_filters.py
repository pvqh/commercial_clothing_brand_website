from playwright.sync_api import Page

from tests.a11y.conftest import assert_no_serious_axe_violations

COATS = "/katalog/shuby/"


def test_listing_with_open_filter_dropdowns(js_enabled: Page, seeded_catalog: str):
    js_enabled.goto(seeded_catalog + COATS)
    for summary in js_enabled.locator("details.filter-bar__group > summary").all():
        summary.click()
    assert_no_serious_axe_violations(js_enabled)


def test_listing_with_active_filters(js_enabled: Page, seeded_catalog: str):
    js_enabled.goto(seeded_catalog + COATS + "?size=m&price_max=200000&sort=price_asc")
    assert_no_serious_axe_violations(js_enabled)


def test_listing_with_no_matching_products(js_enabled: Page, seeded_catalog: str):
    js_enabled.goto(seeded_catalog + COATS + "?size=xxs")
    assert_no_serious_axe_violations(js_enabled)
