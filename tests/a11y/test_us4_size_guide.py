from playwright.sync_api import Page

from tests.a11y.conftest import assert_no_serious_axe_violations


def test_open_size_guide_has_no_serious_violations(js_enabled: Page, seeded_catalog: str):
    js_enabled.goto(seeded_catalog + "/tovar/shuba-iz-norki-klassika/")
    js_enabled.get_by_role("button", name="Таблица размеров").click()
    assert_no_serious_axe_violations(js_enabled)
