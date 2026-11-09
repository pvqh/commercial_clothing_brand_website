import pytest
from playwright.sync_api import Page

from catalog.models import Product
from tests.a11y.conftest import assert_no_serious_axe_violations
from tests.staff_helpers import STAFF_PASSWORD, create_staff


def sign_in(page: Page, base: str) -> None:
    create_staff()
    page.goto(base + "/staff/login/")
    page.locator("#id_username").fill("staff")
    page.locator("#id_password").fill(STAFF_PASSWORD)
    page.get_by_role("button", name="Войти").click()


def test_sign_in_page_has_no_serious_violations(js_enabled: Page, seeded_catalog: str):
    js_enabled.goto(seeded_catalog + "/staff/login/")
    assert_no_serious_axe_violations(js_enabled)


@pytest.mark.parametrize(
    "path",
    ["/staff/catalog/product/", "/staff/audit/changerecord/", "PRODUCT_EDIT"],
)
def test_staff_pages_have_no_serious_violations(js_enabled: Page, seeded_catalog: str, path):
    sign_in(js_enabled, seeded_catalog)
    if path == "PRODUCT_EDIT":
        path = f"/staff/catalog/product/{Product.objects.earliest('id').pk}/change/"
    js_enabled.goto(seeded_catalog + path)
    assert_no_serious_axe_violations(js_enabled)
