"""Browser fixtures shared by tests/e2e and tests/a11y: Playwright Chromium on the live server."""

import os
from collections.abc import Iterator

import pytest
from playwright.sync_api import Browser, Page, sync_playwright

from catalog.management.commands.seed_demo_catalog import seed_demo_catalog

# Playwright's sync API runs an event loop in this thread; Django's ORM calls in the fixtures are
# still synchronous and safe here.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    with sync_playwright() as playwright:
        chromium = playwright.chromium.launch()
        yield chromium
        chromium.close()


def open_page(browser: Browser, *, javascript: bool) -> Iterator[Page]:
    context = browser.new_context(java_script_enabled=javascript, locale="ru-RU")
    page = context.new_page()
    page.set_default_timeout(10_000)
    yield page
    context.close()


@pytest.fixture
def js_enabled(browser: Browser) -> Iterator[Page]:
    yield from open_page(browser, javascript=True)


@pytest.fixture
def js_disabled(browser: Browser) -> Iterator[Page]:
    yield from open_page(browser, javascript=False)


@pytest.fixture(params=["js_enabled", "js_disabled"])
def any_page(request: pytest.FixtureRequest) -> Page:
    """Runs a test once with JavaScript and once without (progressive enhancement, R3)."""
    return request.getfixturevalue(request.param)


@pytest.fixture
def seeded_catalog(transactional_db, live_server) -> str:
    """The demo catalog in the live server's database; returns the server's base address."""
    seed_demo_catalog()
    return live_server.url
