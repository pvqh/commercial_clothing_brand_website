import pytest

from catalog.demo_catalog import build_category, build_published_product

pytestmark = pytest.mark.django_db


@pytest.fixture
def category():
    category = build_category(name_ru="Шубы", name_en="Fur coats")
    build_published_product(category, name_ru="Шуба из норки", name_en="Mink coat")
    return category


def test_russian_and_english_addresses_serve_the_same_category(client, category):
    russian = client.get(f"/katalog/{category.slug_ru}/")
    english = client.get(f"/en/catalog/{category.slug_en}/")
    assert russian.context["category"] == english.context["category"] == category


def test_russian_page_switches_to_the_same_page_in_english(client, category):
    html = client.get(f"/katalog/{category.slug_ru}/").content.decode()
    assert f'href="http://testserver/en/catalog/{category.slug_en}/" hreflang="en"' in html


def test_english_page_switches_to_the_same_page_in_russian(client, category):
    html = client.get(f"/en/catalog/{category.slug_en}/").content.decode()
    assert f'href="http://testserver/katalog/{category.slug_ru}/" hreflang="ru"' in html


def test_english_page_shows_russian_text_where_english_is_blank(client):
    category = build_category(name_ru="Шубы", name_en="Fur coats")
    product = build_published_product(category, name_ru="Шуба из норки", description_en="")
    html = client.get(f"/en/product/{product.slug_en}/").content.decode()
    assert product.description_ru in html


def test_english_page_uses_english_text_when_present(client, category):
    html = client.get(f"/en/catalog/{category.slug_en}/").content.decode()
    assert "<h1>Fur coats</h1>" in html


def test_an_old_russian_slug_redirects_permanently_to_the_current_one(client, category):
    old_slug = category.slug_ru
    category.name_ru = "Меховые шубы"
    category.save()
    response = client.get(f"/katalog/{old_slug}/")
    assert (response.status_code, response["Location"]) == (301, f"/katalog/{category.slug_ru}/")


def test_an_old_english_slug_redirects_within_english(client, category):
    old_slug = category.slug_en
    category.name_en = "Long fur coats"
    category.save()
    response = client.get(f"/en/catalog/{old_slug}/?page=2")
    expected = f"/en/catalog/{category.slug_en}/?page=2"
    assert (response.status_code, response["Location"]) == (301, expected)


def test_an_old_product_slug_redirects_permanently(client):
    category = build_category()
    product = build_published_product(category, name_ru="Шуба из норки")
    old_slug = product.slug_ru
    product.name_ru = "Шуба из соболя"
    product.save()
    response = client.get(f"/tovar/{old_slug}/")
    assert (response.status_code, response["Location"]) == (301, f"/tovar/{product.slug_ru}/")
