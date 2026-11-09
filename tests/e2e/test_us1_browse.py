import re

from playwright.sync_api import Page, expect


def test_shopper_browses_a_category_and_opens_a_product(any_page: Page, seeded_catalog: str):
    page = any_page
    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto(seeded_catalog + "/")

    page.locator(".site-header__nav").get_by_role("link", name="Шубы").click()
    expect(page.get_by_role("heading", level=1)).to_have_text("Шубы")
    expect(page.locator(".product-card")).to_have_count(24)

    page.get_by_role("link", name="Следующая страница").click()
    expect(page).to_have_url(re.compile(r"/katalog/shuby/\?page=2$"))

    page.goto(seeded_catalog + "/katalog/shuby/")
    page.locator(".product-card a").first.click()
    expect(page).to_have_url(re.compile(r"/tovar/"))
    expect(page.locator(".product-gallery img").first).to_be_visible()

    page.get_by_role("navigation", name="Навигационная цепочка").get_by_role(
        "link", name="Шубы"
    ).click()
    expect(page).to_have_url(re.compile(r"/katalog/shuby/$"))
