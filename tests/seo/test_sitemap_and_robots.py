import pytest

from catalog.demo_catalog import build_category, build_product, build_published_product

pytestmark = pytest.mark.django_db


@pytest.fixture
def catalog():
    category = build_category(name_ru="Шубы", name_en="Fur coats")
    published = build_published_product(category, name_ru="Шуба из норки", name_en="Mink coat")
    draft = build_product(name_ru="Черновик")
    hidden = build_category(name_ru="Скрытая", is_published=False)
    return {"category": category, "published": published, "draft": draft, "hidden": hidden}


def sitemap(client) -> str:
    return client.get("/sitemap.xml").content.decode()


def test_the_sitemap_lists_published_categories_in_both_languages(client, catalog):
    xml = sitemap(client)
    category = catalog["category"]
    assert f"/katalog/{category.slug_ru}/" in xml and f"/en/catalog/{category.slug_en}/" in xml


def test_the_sitemap_lists_published_products_in_both_languages(client, catalog):
    xml = sitemap(client)
    product = catalog["published"]
    assert f"/tovar/{product.slug_ru}/" in xml and f"/en/product/{product.slug_en}/" in xml


def test_the_sitemap_has_hreflang_alternates(client, catalog):
    xml = sitemap(client)
    assert 'hreflang="ru"' in xml and 'hreflang="en"' in xml and 'hreflang="x-default"' in xml


def test_the_sitemap_leaves_out_unpublished_items(client, catalog):
    xml = sitemap(client)
    assert catalog["draft"].slug_ru not in xml and catalog["hidden"].slug_ru not in xml


def test_robots_txt_keeps_crawlers_out_of_the_staff_area(client):
    assert "Disallow: /staff/" in client.get("/robots.txt").content.decode()


def test_robots_txt_links_the_sitemap(client):
    assert "Sitemap: http://testserver/sitemap.xml" in client.get("/robots.txt").content.decode()
