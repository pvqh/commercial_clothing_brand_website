"""Shoppers get no cookies and no third-party requests (FR-034, constitution Principle VI)."""

import re

import pytest

from catalog.demo_catalog import build_category, build_published_product

pytestmark = pytest.mark.django_db

EXTERNAL_REFERENCE = re.compile(r'(?:src|href)="(?:https?:)?//(?!testserver[/"])')


@pytest.fixture
def pages():
    category = build_category()
    product = build_published_product(category)
    return [
        "/",
        "/en/",
        f"/katalog/{category.slug_ru}/",
        f"/katalog/{category.slug_ru}/?size=m",
        f"/tovar/{product.slug_ru}/",
        f"/en/product/{product.slug_en}/",
        "/tovar/no-such-product/",
    ]


def test_shopper_pages_set_no_cookies(client, pages):
    for path in pages:
        response = client.get(path, follow=True)
        assert not response.cookies, path


def test_shopper_pages_load_nothing_from_other_sites(client, pages):
    for path in pages:
        html = client.get(path, follow=True).content.decode()
        head_and_body = html.replace('href="http://testserver', 'href="')
        assert not EXTERNAL_REFERENCE.search(head_and_body), path
