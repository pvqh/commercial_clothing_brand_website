"""The five publish rules in data-model.md."""

import pytest

from catalog.demo_catalog import (
    add_to_category,
    build_category,
    build_color,
    build_photo,
    build_product,
    build_product_type,
    build_variant,
)
from catalog.models import Size
from catalog.services.publishing import PublishRuleError, publish, unpublish

pytestmark = pytest.mark.django_db


@pytest.fixture
def ready_product():
    product = build_product()
    add_to_category(product, build_category())
    build_variant(build_color(product), Size.M)
    build_photo(product)
    return product


def failed_rules(product) -> list[str]:
    with pytest.raises(PublishRuleError) as refusal:
        publish(product)
    return refusal.value.failures


def test_a_product_meeting_every_rule_is_published(ready_product):
    publish(ready_product)
    ready_product.refresh_from_db()
    assert ready_product.is_published


def test_publishing_needs_a_category(ready_product):
    ready_product.category_memberships.all().delete()
    assert len(failed_rules(ready_product)) == 1


def test_publishing_needs_a_color_with_a_variant(ready_product):
    ready_product.variants.delete()
    assert len(failed_rules(ready_product)) == 1


def test_publishing_needs_a_photo(ready_product):
    ready_product.photos.all().delete()
    assert len(failed_rules(ready_product)) == 1


def test_publishing_needs_alt_text_on_every_photo(ready_product):
    ready_product.photos.update(alt_text_ru="")
    assert len(failed_rules(ready_product)) == 1


def test_publishing_needs_every_required_russian_text(ready_product):
    ready_product.description_ru = ""
    ready_product.save()
    assert len(failed_rules(ready_product)) == 1


def test_publishing_a_sized_product_needs_a_size_guide(ready_product):
    ready_product.product_type = build_product_type()
    ready_product.product_type.size_guide = None
    ready_product.product_type.save()
    ready_product.save()
    assert len(failed_rules(ready_product)) == 1


def test_a_one_size_product_needs_no_size_guide(ready_product):
    ready_product.variants.update(size=Size.ONE)
    ready_product.product_type.size_guide = None
    ready_product.product_type.save()
    publish(ready_product)
    assert ready_product.is_published


def test_every_failed_rule_is_listed(ready_product):
    ready_product.category_memberships.all().delete()
    ready_product.photos.all().delete()
    assert len(failed_rules(ready_product)) == 2


def test_first_publication_time_is_set_on_the_first_publish(ready_product):
    publish(ready_product)
    assert ready_product.first_published_at is not None


def test_first_publication_time_is_kept_when_republished(ready_product):
    publish(ready_product)
    first_time = ready_product.first_published_at
    unpublish(ready_product)
    publish(ready_product)
    ready_product.refresh_from_db()
    assert ready_product.first_published_at == first_time


def test_unpublishing_hides_the_product(ready_product):
    publish(ready_product)
    unpublish(ready_product)
    ready_product.refresh_from_db()
    assert not ready_product.is_published
