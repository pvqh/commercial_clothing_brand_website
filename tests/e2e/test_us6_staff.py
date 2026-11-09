import re

from playwright.sync_api import Page, expect

from catalog.models import Product
from tests.staff_helpers import STAFF_PASSWORD, create_admin

COAT = "Шуба из норки «Классика»"
NEW_STAFF_PASSWORD = "another-long-password-7"


def sign_in(page: Page, base: str, username: str, password: str) -> None:
    page.goto(base + "/staff/login/")
    page.locator("#id_username").fill(username)
    page.locator("#id_password").fill(password)
    page.get_by_role("button", name="Войти").click()


def create_staff_account(page: Page, base: str) -> None:
    page.goto(base + "/staff/auth/user/add/")
    page.locator("#id_username").fill("maria")
    page.locator("#id_first_name").fill("Мария")
    page.locator("#id_password1").fill(NEW_STAFF_PASSWORD)
    page.locator("#id_password2").fill(NEW_STAFF_PASSWORD)
    page.get_by_role("button", name="Сохранить", exact=True).click()
    expect(page.locator(".messagelist")).to_be_visible()


def edit_price_and_stock(page: Page, base: str) -> None:
    coat = Product.objects.get(name_ru=COAT)
    color = coat.colors.get(position=0)
    page.goto(f"{base}/staff/catalog/color/{color.pk}/change/")
    page.locator("input[name$='-0-price_rub']").fill("175000")
    page.locator("input[name$='-0-stock']").fill("9")
    page.get_by_role("button", name="Сохранить", exact=True).click()
    expect(page.locator(".messagelist")).to_be_visible()


def edit_description_and_delete_photo(page: Page, base: str) -> None:
    coat = Product.objects.get(name_ru=COAT)
    page.goto(f"{base}/staff/catalog/product/{coat.pk}/change/")
    page.locator("textarea[name='description_ru']").fill("Обновлённое описание шубы.")
    page.locator("input[name$='-DELETE']").last.check()
    page.get_by_role("button", name="Сохранить", exact=True).click()
    expect(page.locator(".messagelist")).to_be_visible()


def unpublish_coat(page: Page, base: str) -> None:
    page.goto(base + "/staff/catalog/product/?q=" + "Классика")
    page.locator("input[name='_selected_action']").first.check()
    page.locator("select[name='action']").select_option("unpublish_selected")
    page.locator("button[name='index']").click()
    expect(page.locator(".messagelist")).to_be_visible()


def test_staff_maintain_the_catalog_and_undo_a_change(js_enabled: Page, seeded_catalog: str):
    page, base = js_enabled, seeded_catalog
    create_admin()
    sign_in(page, base, "admin", STAFF_PASSWORD)
    create_staff_account(page, base)
    page.context.clear_cookies()

    sign_in(page, base, "maria", NEW_STAFF_PASSWORD)
    edit_price_and_stock(page, base)
    edit_description_and_delete_photo(page, base)
    unpublish_coat(page, base)

    page.goto(base + "/staff/audit/changerecord/?field_name=price_kopecks")
    expect(page.locator("#result_list")).to_contain_text("Мария")
    page.get_by_role("button", name=re.compile("Отменить")).first.click()
    expect(page.locator(".messagelist")).to_contain_text("Изменение отменено")
    coat = Product.objects.get(name_ru=COAT)
    first_size = coat.colors.get(position=0).variants.order_by("size")[0]
    assert first_size.price_kopecks != 17_500_000
