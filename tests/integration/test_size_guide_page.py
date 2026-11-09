import pytest

from catalog.demo_catalog import build_category, build_published_product
from catalog.models import Size

pytestmark = pytest.mark.django_db


@pytest.fixture
def category():
    return build_category()


def page_html(client, product, language_prefix: str = "") -> str:
    slug = product.slug_en if language_prefix else product.slug_ru
    path = f"{language_prefix}/product/{slug}/" if language_prefix else f"/tovar/{slug}/"
    return client.get(path).content.decode()


def test_a_sized_product_page_contains_its_size_guide(client, category):
    coat = build_published_product(category, sizes=[Size.S, Size.M])
    html = page_html(client, coat)
    guide = coat.effective_size_guide
    assert 'class="size-guide' in html
    for row in guide.rows.all():
        assert str(row.chest_cm).replace(".", ",") in html


@pytest.mark.parametrize("heading", ["Грудь", "Талия", "Бёдра", "Рукав", "Длина"])
def test_the_guide_shows_every_measurement(client, category, heading):
    coat = build_published_product(category, sizes=[Size.M])
    assert heading in page_html(client, coat)


def test_the_guide_shows_inches_too(client, category):
    coat = build_published_product(category, sizes=[Size.M])
    assert "31,5" in page_html(client, coat)


def test_the_guide_explains_how_to_measure_in_the_page_language(client, category):
    coat = build_published_product(category, sizes=[Size.M])
    assert "Measure around the fullest part" in page_html(client, coat, "/en")


def test_a_one_size_product_has_no_selector_and_no_guide(client, category):
    scarf = build_published_product(category, sizes=[Size.ONE])
    html = page_html(client, scarf)
    assert 'name="size"' not in html and 'class="size-guide' not in html
