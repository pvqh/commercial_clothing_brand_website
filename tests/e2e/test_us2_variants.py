import re

from playwright.sync_api import Page, expect

COAT = "/tovar/shuba-iz-norki-klassika/"


def size_option(page: Page, label: str):
    sizes = page.locator("fieldset.size-selector")
    return sizes.get_by_role("radio", name=re.compile(rf"^{label}\b"))


def test_shopper_switches_colors_and_chooses_a_size(any_page: Page, seeded_catalog: str):
    page = any_page
    page.goto(seeded_catalog + COAT)
    expect(size_option(page, "S")).to_be_enabled()

    page.get_by_role("link", name=re.compile("Графит")).click()
    expect(page.get_by_role("link", name=re.compile("Графит"))).to_have_attribute(
        "aria-current", "true"
    )
    expect(size_option(page, "S")).to_be_disabled()
    expect(page.locator("fieldset.size-selector")).to_contain_text("Нет в наличии")

    size_option(page, "M").check()
    expect(page.locator(".product-page__price")).to_contain_text("190 000 ₽", use_inner_text=True)
    expect(page.locator(".product-page__price")).not_to_contain_text("от", use_inner_text=True)


def test_an_out_of_stock_color_is_labelled(any_page: Page, seeded_catalog: str):
    any_page.goto(seeded_catalog + COAT)
    expect(any_page.get_by_role("link", name=re.compile("Карамель"))).to_contain_text(
        "Нет в наличии"
    )
