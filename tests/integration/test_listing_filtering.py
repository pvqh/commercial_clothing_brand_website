from datetime import timedelta

import pytest

from catalog.demo_catalog import build_category, build_color, build_published_product, build_variant
from catalog.models import Size

pytestmark = pytest.mark.django_db


@pytest.fixture
def category():
    return build_category(name_ru="Шубы")


def listing(client, category, query: str = ""):
    return client.get(f"/katalog/{category.slug_ru}/{query}")


def listed_names(response) -> list[str]:
    return [product.name_ru for product in response.context["page_obj"].object_list]


def coat(category, name: str, sizes: list[Size], price_rub: int, stock: int = 1, days: int = 0):
    return build_published_product(
        category,
        name_ru=name,
        sizes=sizes,
        price_kopecks=price_rub * 100,
        stock=stock,
        age=timedelta(days=days),
    )


def test_a_size_filter_shows_products_with_that_size_in_stock(client, category):
    coat(category, "L в наличии", [Size.L], 100_000)
    coat(category, "Только M", [Size.M], 100_000)
    coat(category, "L нет", [Size.L], 100_000, stock=0)
    assert listed_names(listing(client, category, "?size=l")) == ["L в наличии"]


def test_a_size_in_stock_in_any_color_counts(client, category):
    product = coat(category, "Два цвета", [Size.M], 100_000)
    build_variant(build_color(product), Size.L, stock=2)
    assert listed_names(listing(client, category, "?size=l")) == ["Два цвета"]


def test_several_sizes_match_any_of_them(client, category):
    coat(category, "M", [Size.M], 100_000, days=1)
    coat(category, "L", [Size.L], 100_000, days=2)
    coat(category, "S", [Size.S], 100_000, days=3)
    assert listed_names(listing(client, category, "?size=m&size=l")) == ["M", "L"]


def test_the_price_range_is_inclusive(client, category):
    coat(category, "100", [Size.M], 100_000, days=1)
    coat(category, "150", [Size.M], 150_000, days=2)
    coat(category, "151", [Size.M], 151_000, days=3)
    names = listed_names(listing(client, category, "?price_min=100000&price_max=150000"))
    assert names == ["100", "150"]


def test_size_and_price_apply_to_the_same_variant(client, category):
    product = coat(category, "M дешёвая, L дорогая", [Size.M], 90_000)
    build_variant(product.colors.get(), Size.L, price_kopecks=200_000_00, stock=1)
    assert listed_names(listing(client, category, "?size=m&price_min=150000")) == []
    assert listed_names(listing(client, category, "?size=l&price_min=150000")) != []


def test_price_sorts_use_the_lowest_matching_in_stock_price(client, category):
    cheap_l = coat(category, "Дешёвая L", [Size.L], 120_000)
    build_variant(cheap_l.colors.get(), Size.S, price_kopecks=50_000_00, stock=1)
    coat(category, "Средняя L", [Size.L], 100_000)
    names = listed_names(listing(client, category, "?size=l&sort=price_asc"))
    assert names == ["Средняя L", "Дешёвая L"]


def test_price_high_to_low(client, category):
    coat(category, "Дешёвая", [Size.M], 100_000)
    coat(category, "Дорогая", [Size.M], 300_000)
    assert listed_names(listing(client, category, "?sort=price_desc")) == ["Дорогая", "Дешёвая"]


def test_sold_out_products_are_hidden_while_a_filter_is_active(client, category):
    coat(category, "Распродана", [Size.M], 100_000, stock=0)
    assert listed_names(listing(client, category, "?price_max=500000")) == []


def test_sold_out_products_sort_last_by_price_without_a_filter(client, category):
    coat(category, "Распродана", [Size.M], 10_000, stock=0)
    coat(category, "В наличии", [Size.M], 200_000)
    assert listed_names(listing(client, category, "?sort=price_asc")) == ["В наличии", "Распродана"]


def test_only_sizes_present_in_the_category_are_offered(client, category):
    coat(category, "M", [Size.M], 100_000)
    coat(category, "XL", [Size.XL], 100_000)
    other = build_category(name_ru="Другая")
    coat(other, "S", [Size.S], 100_000)
    assert list(listing(client, category).context["offered_sizes"]) == [Size.M, Size.XL]


def test_a_non_normalised_query_redirects(client, category):
    coat(category, "M", [Size.M], 100_000)
    response = listing(client, category, "?price_min=200000&price_max=100000&size=zz&page=99")
    expected = f"/katalog/{category.slug_ru}/?price_min=100000&price_max=200000"
    assert (response.status_code, response["Location"]) == (302, expected)


def test_no_match_shows_a_message_and_a_clear_all_link(client, category):
    coat(category, "M", [Size.M], 100_000)
    html = listing(client, category, "?size=xxs").content.decode()
    assert "Нет товаров, подходящих под фильтры" in html
    assert f'href="/katalog/{category.slug_ru}/"' in html


def test_filtered_views_are_not_indexed_and_point_to_the_unfiltered_page(client, category):
    coat(category, "M", [Size.M], 100_000)
    html = listing(client, category, "?size=m").content.decode()
    assert '<meta name="robots" content="noindex, follow">' in html
    expected = f'<link rel="canonical" href="http://testserver/katalog/{category.slug_ru}/">'
    assert expected in html


def test_sorted_views_are_not_indexed(client, category):
    coat(category, "M", [Size.M], 100_000)
    html = listing(client, category, "?sort=price_asc").content.decode()
    assert '<meta name="robots" content="noindex, follow">' in html


def test_the_result_count_reflects_the_filter(client, category):
    coat(category, "M", [Size.M], 100_000)
    coat(category, "L", [Size.L], 100_000)
    assert "1 товар" in listing(client, category, "?size=m").content.decode()


def test_the_card_price_is_the_lowest_matching_price(client, category):
    product = coat(category, "Шуба", [Size.S], 90_000)
    build_variant(product.colors.get(), Size.L, price_kopecks=120_000_00, stock=1)
    html = listing(client, category, "?size=l").content.decode()
    assert "120 000 ₽" in html and "90 000" not in html
