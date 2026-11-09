import pytest


@pytest.fixture(autouse=True)
def isolated_media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    return settings.MEDIA_ROOT


from tests.browser_fixtures import (  # noqa: E402, F401  (fixtures for tests/e2e and tests/a11y)
    any_page,
    browser,
    js_disabled,
    js_enabled,
    seeded_catalog,
)
