import re

from playwright.sync_api import Browser, Page, expect

COATS = "/katalog/shuby/"


def open_filter(page: Page, name: str) -> None:
    page.locator("details.filter-bar__group", has_text=name).locator("summary").click()


def show_results(page: Page) -> None:
    page.get_by_role("button", name="Показать").click()


def apply_sizes_and_price(page: Page) -> None:
    open_filter(page, "Размер")
    page.get_by_label("M", exact=True).check()
    page.get_by_label("L", exact=True).check()
    open_filter(page, "Цена")
    page.get_by_label("от", exact=True).fill("100000")
    page.get_by_label("до", exact=True).fill("200000")
    show_results(page)


def test_shopper_filters_sorts_and_shares_the_address(
    any_page: Page, seeded_catalog: str, browser: Browser
):
    page = any_page
    page.goto(seeded_catalog + COATS)
    apply_sizes_and_price(page)
    expect(page).to_have_url(re.compile(r"\?size=m&size=l&price_min=100000&price_max=200000$"))

    page.get_by_label("Сортировка").select_option("price_asc")
    show_results(page)
    expect(page).to_have_url(re.compile(r"sort=price_asc$"))
    first_card_name = page.locator(".product-card__title").first.text_content() or ""

    shared = browser.new_page()
    shared.goto(page.url)
    expect(shared.locator(".product-card__title").first).to_have_text(first_card_name)
    shared.close()

    page.get_by_role("link", name=re.compile("Убрать фильтр: M")).click()
    expect(page).not_to_have_url(re.compile(r"size=m"))
    page.go_back()
    expect(page).to_have_url(re.compile(r"size=m"))

    page.get_by_role("link", name="Сбросить все").first.click()
    expect(page).to_have_url(re.compile(r"/katalog/shuby/$"))
