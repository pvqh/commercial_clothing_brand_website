import json
import re
from datetime import timedelta

import pytest

from catalog.demo_catalog import build_category, build_color, build_published_product, build_variant
from catalog.models import Size

pytestmark = pytest.mark.django_db


@pytest.fixture
def category():
    return build_category(name_ru="Шубы", name_en="Fur coats")


@pytest.fixture
def product(category):
    return build_published_product(category, name_ru="Шуба из норки", name_en="Mink coat")


def html_of(client, url: str) -> str:
    return client.get(url).content.decode()


def head_of(html: str) -> str:
    return html.split("</head>", 1)[0]


def json_ld_blocks(html: str) -> list[dict]:
    scripts = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    return [json.loads(script) for script in scripts]


def json_ld_of_type(html: str, schema_type: str) -> dict:
    return next(block for block in json_ld_blocks(html) if block["@type"] == schema_type)


def title_of(html: str) -> str:
    match = re.search(r"<title>(.*?)</title>", html, re.S)
    assert match, "page has no <title>"
    return match.group(1).strip()


def test_listing_and_product_pages_have_distinct_titles(client, category, product):
    listing = html_of(client, f"/katalog/{category.slug_ru}/")
    product_page = html_of(client, f"/tovar/{product.slug_ru}/")
    assert title_of(listing) != title_of(product_page)


def test_listing_page_two_has_its_own_title(client, category):
    for day in range(25):
        build_published_product(category, age=timedelta(days=day))
    first = html_of(client, f"/katalog/{category.slug_ru}/")
    second = html_of(client, f"/katalog/{category.slug_ru}/?page=2")
    assert title_of(first) != title_of(second)


def test_every_page_has_a_meta_description(client, category, product):
    for url in (f"/katalog/{category.slug_ru}/", f"/tovar/{product.slug_ru}/"):
        assert re.search(r'<meta name="description" content="[^"]+">', html_of(client, url))


def test_canonical_is_the_page_without_query(client, category, product):
    html = html_of(client, f"/tovar/{product.slug_ru}/?utm_source=x")
    assert f'<link rel="canonical" href="http://testserver/tovar/{product.slug_ru}/">' in html


def test_canonical_keeps_the_page_number_from_page_two(client, category):
    for day in range(25):
        build_published_product(category, age=timedelta(days=day))
    html = html_of(client, f"/katalog/{category.slug_ru}/?page=2")
    expected = f'<link rel="canonical" href="http://testserver/katalog/{category.slug_ru}/?page=2">'
    assert expected in html


@pytest.mark.parametrize("language", ["ru", "en", "x-default"])
def test_pages_list_language_alternates(client, product, language):
    head = head_of(html_of(client, f"/tovar/{product.slug_ru}/"))
    assert f'<link rel="alternate" hreflang="{language}"' in head


def test_x_default_points_to_russian(client, product):
    head = head_of(html_of(client, f"/en/product/{product.slug_en}/"))
    expected = f'hreflang="x-default" href="http://testserver/tovar/{product.slug_ru}/"'
    assert expected in head


@pytest.mark.parametrize("prop", ["og:title", "og:description", "og:url", "og:image", "og:locale"])
def test_product_page_has_open_graph_tags(client, product, prop):
    assert f'<meta property="{prop}"' in head_of(html_of(client, f"/tovar/{product.slug_ru}/"))


@pytest.mark.parametrize("prop", ["og:title", "og:description", "og:url", "og:locale"])
def test_listing_page_has_open_graph_tags(client, category, product, prop):
    assert f'<meta property="{prop}"' in head_of(html_of(client, f"/katalog/{category.slug_ru}/"))


def test_product_json_ld_has_a_single_offer_in_rubles(client, product):
    data = json_ld_of_type(html_of(client, f"/tovar/{product.slug_ru}/"), "Product")
    assert (data["offers"]["@type"], data["offers"]["priceCurrency"]) == ("Offer", "RUB")
    assert data["offers"]["price"] == "125000"


def test_product_json_ld_has_an_aggregate_offer_when_prices_differ(client, product):
    build_variant(product.colors.first(), Size.XL, price_kopecks=15_000_000)
    offers = json_ld_of_type(html_of(client, f"/tovar/{product.slug_ru}/"), "Product")["offers"]
    assert (offers["@type"], offers["lowPrice"], offers["highPrice"]) == (
        "AggregateOffer",
        "125000",
        "150000",
    )


def test_product_json_ld_names_the_product_and_its_sku(client, product):
    data = json_ld_of_type(html_of(client, f"/tovar/{product.slug_ru}/"), "Product")
    assert (data["name"], data["sku"]) == ("Шуба из норки", str(product.pk))


def test_breadcrumb_json_ld_runs_home_category_product(client, category, product):
    color = build_color(product)
    build_variant(color)
    data = json_ld_of_type(html_of(client, f"/tovar/{product.slug_ru}/"), "BreadcrumbList")
    names = [item["name"] for item in data["itemListElement"]]
    assert names[1:] == ["Шубы", "Шуба из норки"]
