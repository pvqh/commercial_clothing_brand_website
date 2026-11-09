from datetime import timedelta

import pytest
from django.urls import reverse

from catalog.demo_catalog import build_category, build_product, build_published_product

pytestmark = pytest.mark.django_db


def category_url(category, query: str = "") -> str:
    return reverse("catalog:category", kwargs={"slug": category.slug_ru}) + query


def listed_ids(response) -> list[int]:
    return [product.pk for product in response.context["page_obj"].object_list]


@pytest.fixture
def category():
    return build_category(name_ru="Шубы")


def test_only_published_products_are_listed(client, category):
    published = build_published_product(category)
    draft = build_product()
    draft.category_memberships.create(category=category)
    assert listed_ids(client.get(category_url(category))) == [published.pk]


def test_products_are_listed_newest_first(client, category):
    older = build_published_product(category, age=timedelta(days=5))
    newer = build_published_product(category, age=timedelta(days=1))
    assert listed_ids(client.get(category_url(category))) == [newer.pk, older.pk]


def test_products_published_at_the_same_time_are_ordered_by_id_descending(client, category):
    first = build_published_product(category)
    second = build_published_product(category)
    second.first_published_at = first.first_published_at
    second.save()
    assert listed_ids(client.get(category_url(category))) == [second.pk, first.pk]


def test_a_page_shows_24_products(client, category):
    for day in range(26):
        build_published_product(category, age=timedelta(days=day))
    assert len(listed_ids(client.get(category_url(category)))) == 24


def test_page_two_shows_the_remaining_products(client, category):
    for day in range(26):
        build_published_product(category, age=timedelta(days=day))
    assert len(listed_ids(client.get(category_url(category, "?page=2")))) == 2


def test_page_one_redirects_to_the_address_without_a_page(client, category):
    build_published_product(category)
    response = client.get(category_url(category, "?page=1"))
    assert (response.status_code, response["Location"]) == (302, category_url(category))


def test_a_page_beyond_the_last_redirects_to_the_last_page(client, category):
    for day in range(26):
        build_published_product(category, age=timedelta(days=day))
    response = client.get(category_url(category, "?page=99"))
    assert (response.status_code, response["Location"]) == (302, category_url(category, "?page=2"))


def test_an_unpublished_category_is_not_found(client):
    hidden = build_category(is_published=False)
    assert client.get(category_url(hidden)).status_code == 404


def test_an_empty_published_category_is_shown_but_not_indexed(client, category):
    response = client.get(category_url(category))
    assert response.status_code == 200
    assert '<meta name="robots" content="noindex, follow">' in response.content.decode()


def test_a_category_without_published_products_is_hidden_from_navigation(client, category):
    filled = build_category(name_ru="Аксессуары")
    build_published_product(filled)
    navigation = list(client.get(category_url(filled)).context["navigation_categories"])
    assert navigation == [filled]


def test_listing_is_cacheable_for_a_minute_and_sets_no_cookie(client, category):
    build_published_product(category)
    response = client.get(category_url(category))
    assert response["Cache-Control"] == "public, max-age=60"
    assert not response.cookies
