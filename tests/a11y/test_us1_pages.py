import pytest
from playwright.sync_api import Page

from tests.a11y.conftest import assert_no_serious_axe_violations


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/en/",
        "/katalog/shuby/",
        "/katalog/shuby/?page=2",
        "/tovar/shuba-iz-norki-klassika/",
        "/en/product/classic-mink-coat/",
        "/tovar/does-not-exist/",
    ],
)
def test_us1_pages_have_no_serious_accessibility_violations(
    js_enabled: Page, seeded_catalog: str, path: str
):
    js_enabled.goto(seeded_catalog + path)
    assert_no_serious_axe_violations(js_enabled)
