import json
import re

import pytest

from catalog.demo_catalog import (
    build_category,
    build_color,
    build_photo,
    build_published_product,
    build_variant,
)
from catalog.models import Size

pytestmark = pytest.mark.django_db


@pytest.fixture
def category():
    return build_category(name_ru="Шубы")


@pytest.fixture
def coat(category):
    product = build_published_product(category, name_ru="Шуба", sizes=[Size.S, Size.M])
    natural = product.colors.get()
    natural.variants.filter(size=Size.M).update(stock=0)
    graphite = build_color(product, name_ru="Графит", name_en="Graphite")
    build_variant(graphite, Size.S, stock=0)
    build_variant(graphite, Size.M, stock=0)
    build_photo(product, color=graphite, alt_text_ru="Шуба, графит")
    return product


def page(client, product, query: str = ""):
    return client.get(f"/tovar/{product.slug_ru}/{query}")


def size_input(html: str, code: str) -> str:
    match = re.search(rf'<input[^>]*name="size"[^>]*value="{code}"[^>]*>', html)
    assert match, f"no size input for {code}"
    return match.group(0)


def test_choosing_a_color_shows_that_colors_photos(client, coat):
    graphite = coat.colors.get(name_ru="Графит")
    html = page(client, coat, f"?color={graphite.pk}").content.decode()
    assert "Шуба, графит" in html


def test_a_color_without_photos_shows_the_shared_photos(client, coat):
    natural = coat.colors.get(position=0)
    html = page(client, coat, f"?color={natural.pk}").content.decode()
    assert "Шуба, графит" not in html and coat.photos.get(color=None).alt_text_ru in html


def test_an_out_of_stock_size_is_disabled_and_labelled(client, coat):
    html = page(client, coat).content.decode()
    assert "disabled" in size_input(html, "m")
    assert "Нет в наличии" in html


def test_an_in_stock_size_can_be_chosen(client, coat):
    assert "disabled" not in size_input(page(client, coat).content.decode(), "s")


def test_a_color_with_no_stock_is_labelled_out_of_stock(client, coat):
    html = page(client, coat).content.decode()
    graphite_link = re.search(
        r'<a[^>]*class="color-options__option[^"]*"[^>]*>.*?Графит.*?</a>', html, re.S
    )
    assert "Нет в наличии" in graphite_link.group(0)


def test_the_selected_color_is_marked_current(client, coat):
    graphite = coat.colors.get(name_ru="Графит")
    html = page(client, coat, f"?color={graphite.pk}").content.decode()
    current = re.search(r'<a[^>]*aria-current="true"[^>]*>.*?</a>', html, re.S).group(0)
    assert "Графит" in current


def test_an_unknown_color_redirects_to_the_address_without_it(client, coat):
    response = page(client, coat, "?color=999999")
    assert (response.status_code, response["Location"]) == (302, f"/tovar/{coat.slug_ru}/")


def test_a_color_of_another_product_redirects(client, coat, category):
    other = build_published_product(category)
    response = page(client, coat, f"?color={other.colors.get().pk}")
    assert response.status_code == 302


def test_a_sold_out_product_page_is_still_shown(client, coat):
    coat.variants.update(stock=0)
    response = page(client, coat)
    assert response.status_code == 200 and "Нет в наличии" in response.content.decode()


def test_a_sold_out_product_page_says_sold_out(client, coat):
    coat.variants.update(stock=0)
    assert "Распродано" in page(client, coat).content.decode()


def test_a_sold_out_product_is_out_of_stock_in_structured_data(client, coat):
    coat.variants.update(stock=0)
    html = page(client, coat).content.decode()
    data = json.loads(
        re.search(r'<script type="application/ld\+json">(.*?)</script>', html).group(1)
    )
    assert data["offers"]["availability"] == "https://schema.org/OutOfStock"


def test_a_sold_out_product_card_says_sold_out(client, coat, category):
    coat.variants.update(stock=0)
    html = client.get(f"/katalog/{category.slug_ru}/").content.decode()
    assert "Распродано" in html


def test_a_single_color_product_has_no_color_selector(client, category):
    product = build_published_product(category)
    assert "color-options" not in page(client, product).content.decode()


def test_a_one_size_product_has_no_size_selector(client, category):
    scarf = build_published_product(category, sizes=[Size.ONE])
    assert 'name="size"' not in page(client, scarf).content.decode()


def test_a_color_view_is_not_indexed_and_points_to_the_product(client, coat):
    graphite = coat.colors.get(name_ru="Графит")
    html = page(client, coat, f"?color={graphite.pk}").content.decode()
    assert '<meta name="robots" content="noindex, follow">' in html
    assert f'<link rel="canonical" href="http://testserver/tovar/{coat.slug_ru}/">' in html


def test_each_in_stock_size_has_its_exact_price_on_the_page(client, coat):
    coat.variants.filter(size=Size.S).update(price_kopecks=11_000_000)
    html = page(client, coat).content.decode()
    assert 'data-size="s"' in html and "110 000 ₽" in html
