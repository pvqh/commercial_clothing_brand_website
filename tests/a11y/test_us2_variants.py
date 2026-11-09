from playwright.sync_api import Page

from catalog.models import Color
from tests.a11y.conftest import assert_no_serious_axe_violations

COAT = "/tovar/shuba-iz-norki-klassika/"


def test_coat_with_a_color_selected_has_no_serious_violations(js_enabled: Page, seeded_catalog):
    graphite = Color.objects.get(name_ru="Графит")
    js_enabled.goto(f"{seeded_catalog}{COAT}?color={graphite.pk}")
    js_enabled.locator("fieldset.size-selector input:not([disabled])").first.check()
    assert_no_serious_axe_violations(js_enabled)


def test_sold_out_product_has_no_serious_violations(js_enabled: Page, seeded_catalog):
    js_enabled.goto(seeded_catalog + "/tovar/shuba-iz-sobolya/")
    assert_no_serious_axe_violations(js_enabled)
