"""A shopper using only the keyboard can browse, filter, choose options and read the size guide."""

import re
from collections.abc import Callable

from playwright.sync_api import Page, expect

MAX_TABS = 120


def focused(page: Page, check: str) -> bool:
    return page.evaluate(f"(() => {{ const el = document.activeElement; return {check}; }})()")


def tab_to(page: Page, check: str) -> None:
    """Presses Tab until the focused element passes the JavaScript `check`, asserting focus is
    always visible on the way (WCAG 2.4.7)."""
    for _ in range(MAX_TABS):
        page.keyboard.press("Tab")
        assert focused(page, "el === document.body || el.matches(':focus-visible')")
        if focused(page, check):
            return
    raise AssertionError(f"Keyboard focus never reached: {check}")


def text_is(text: str) -> str:
    return f"el.textContent.trim().startsWith({text!r})"


def press_on(page: Page, check: str, key: str = "Enter", then: Callable | None = None) -> None:
    tab_to(page, check)
    page.keyboard.press(key)
    if then:
        then()


def test_keyboard_only_shopping_journey(js_enabled: Page, seeded_catalog: str):
    page = js_enabled
    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto(seeded_catalog + "/")

    press_on(page, "el.matches('.site-header__nav a') && " + text_is("Шубы"))
    expect(page).to_have_url(seeded_catalog + "/katalog/shuby/")

    press_on(page, "el.matches('.filter-bar__group > summary') && " + text_is("Размер"))
    settle = page.wait_for_load_state  # HTMX refreshes the results after every change
    press_on(
        page, "el.matches('input[name=size][value=m]')", "Space", lambda: settle("networkidle")
    )
    press_on(page, "el.matches('select[name=sort]')", "ArrowDown", lambda: settle("networkidle"))
    press_on(page, "el.matches('.filter-bar__submit')")
    expect(page).to_have_url(seeded_catalog + "/katalog/shuby/?size=m&sort=price_asc")

    press_on(page, "el.matches('.product-card__link')")
    expect(page).to_have_url(re.compile(r"/tovar/"))
    page.goto(seeded_catalog + "/tovar/shuba-iz-norki-klassika/")

    press_on(page, "el.matches('.color-options__option') && " + text_is("Графит"))
    settle("networkidle")
    press_on(page, "el.matches('input[name=size]')", key="Space")
    expect(page.locator("input[name=size]:checked")).to_have_count(1)

    press_on(page, "el.matches('.size-guide__open')")
    expect(page.get_by_role("dialog")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog")).to_be_hidden()
    assert focused(page, "el.matches('.size-guide__open')")
