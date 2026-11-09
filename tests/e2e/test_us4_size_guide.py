from playwright.sync_api import Page, expect

COAT = "/tovar/shuba-iz-norki-klassika/"


def choose_graphite_and_m(page: Page) -> None:
    graphite = page.get_by_role("link", name="Графит")
    graphite.click()
    expect(graphite).to_have_attribute("aria-current", "true")  # HTMX swap finished
    page.locator("fieldset.size-selector input[value='m']").check()


def test_size_guide_opens_in_a_dialog_and_keeps_choices(js_enabled: Page, seeded_catalog: str):
    page = js_enabled
    page.goto(seeded_catalog + COAT)
    choose_graphite_and_m(page)
    opener = page.get_by_role("button", name="Таблица размеров")

    opener.click()
    dialog = page.get_by_role("dialog")
    expect(dialog).to_be_visible()
    expect(dialog).to_contain_text("Грудь")
    page.keyboard.press("Escape")
    expect(dialog).to_be_hidden()
    expect(opener).to_be_focused()

    opener.click()
    dialog.get_by_role("button", name="Закрыть").click()
    expect(dialog).to_be_hidden()
    expect(opener).to_be_focused()

    expect(page.get_by_role("link", name="Графит")).to_have_attribute("aria-current", "true")
    expect(page.locator("fieldset.size-selector input[value='m']")).to_be_checked()


def test_size_guide_is_readable_without_javascript(js_disabled: Page, seeded_catalog: str):
    page = js_disabled
    page.goto(seeded_catalog + COAT)
    page.locator("details.size-guide__fallback > summary").click()
    expect(page.locator("details.size-guide__fallback table")).to_be_visible()
