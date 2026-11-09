import pytest

from catalog.demo_catalog import build_color, build_product, build_variant
from catalog.models import Size
from catalog.services.product_availability import availability_for, color_states, price_range

pytestmark = pytest.mark.django_db


@pytest.fixture
def coat():
    product = build_product()
    natural = build_color(product, name_ru="Натуральный")
    graphite = build_color(product, name_ru="Графит")
    build_variant(natural, Size.L, price_kopecks=13_000_000, stock=0)
    build_variant(natural, Size.S, price_kopecks=12_000_000, stock=2)
    build_variant(natural, Size.M, price_kopecks=12_500_000, stock=1)
    build_variant(graphite, Size.M, price_kopecks=12_500_000, stock=0)
    return product


def test_sizes_come_in_scale_order(coat):
    options = availability_for(coat, coat.colors.get(name_ru="Натуральный"))
    assert [option.size for option in options] == [Size.S, Size.M, Size.L]


def test_each_size_reports_whether_it_is_in_stock(coat):
    options = availability_for(coat, coat.colors.get(name_ru="Натуральный"))
    assert [option.in_stock for option in options] == [True, True, False]


def test_each_size_carries_its_exact_price(coat):
    options = availability_for(coat, coat.colors.get(name_ru="Натуральный"))
    assert [option.price_kopecks for option in options] == [12_000_000, 12_500_000, 13_000_000]


def test_size_options_belong_to_the_chosen_color_only(coat):
    options = availability_for(coat, coat.colors.get(name_ru="Графит"))
    assert [(option.size, option.in_stock) for option in options] == [(Size.M, False)]


def test_a_color_is_out_of_stock_when_all_its_sizes_are(coat):
    states = {state.color.name_ru: state.is_out_of_stock for state in color_states(coat)}
    assert states == {"Натуральный": False, "Графит": True}


def test_colors_come_in_position_order(coat):
    assert [state.color.name_ru for state in color_states(coat)] == ["Натуральный", "Графит"]


def test_product_is_sold_out_when_every_variant_has_zero_stock(coat):
    coat.variants.update(stock=0)
    assert coat.is_sold_out


def test_product_is_not_sold_out_while_one_variant_has_stock(coat):
    assert not coat.is_sold_out


def test_price_range_covers_in_stock_variants_only(coat):
    prices = price_range(coat)
    assert (prices.low_kopecks, prices.high_kopecks, prices.is_from) == (
        12_000_000,
        12_500_000,
        True,
    )


def test_price_range_of_a_color_covers_that_color_only(coat):
    prices = price_range(coat, coat.colors.get(name_ru="Графит"))
    assert (prices.low_kopecks, prices.is_from, prices.sold_out) == (12_500_000, False, True)


def test_price_range_of_a_sold_out_product_covers_all_variants(coat):
    coat.variants.update(stock=0)
    prices = price_range(coat)
    assert (prices.low_kopecks, prices.high_kopecks, prices.sold_out) == (
        12_000_000,
        13_000_000,
        True,
    )
