from decimal import Decimal

import pytest
from django.utils import translation

from catalog.demo_catalog import build_product, build_product_type, build_size_guide
from catalog.models import Size
from catalog.services.size_guides import inches, size_guide_table

pytestmark = pytest.mark.django_db


def test_the_product_override_wins_over_the_product_type_guide():
    override = build_size_guide([Size.M])
    product = build_product(product_type=build_product_type(), size_guide=override)
    assert product.effective_size_guide == override


def test_the_product_type_guide_is_used_without_an_override():
    product_type = build_product_type()
    assert build_product(product_type=product_type).effective_size_guide == product_type.size_guide


def test_inches_are_centimetres_divided_by_2_54_to_one_decimal():
    assert inches(Decimal("88.0")) == Decimal("34.6")


def test_rows_come_in_size_scale_order():
    guide = build_size_guide([Size.L, Size.S, Size.M])
    product = build_product(product_type=build_product_type(guide))
    assert [row.size for row in size_guide_table(product).rows] == [Size.S, Size.M, Size.L]


def test_each_row_has_centimetres_and_inches():
    product = build_product(product_type=build_product_type(build_size_guide([Size.S])))
    measurement = size_guide_table(product).rows[0].measurements[0]
    assert (measurement.cm, measurement.inches) == (Decimal("80.0"), Decimal("31.5"))


def test_how_to_measure_follows_the_page_language():
    product = build_product(product_type=build_product_type(build_size_guide([Size.S])))
    with translation.override("en"):
        assert size_guide_table(product).how_to_measure.startswith("Measure")


def test_a_product_without_a_guide_has_no_table():
    product_type = build_product_type()
    product_type.size_guide = None
    product_type.save()
    assert size_guide_table(build_product(product_type=product_type)) is None
