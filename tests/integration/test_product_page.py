import pytest
from django.urls import reverse

from catalog.demo_catalog import (
    add_to_category,
    build_category,
    build_photo,
    build_product,
    build_published_product,
)
from catalog.models import FurTreatment

pytestmark = pytest.mark.django_db


def product_url(product) -> str:
    return reverse("catalog:product", kwargs={"slug": product.slug_ru})


@pytest.fixture
def coats():
    return build_category(name_ru="Шубы")


@pytest.fixture
def product(coats):
    product = build_published_product(
        coats,
        name_ru="Шуба из норки",
        fur_treatment=FurTreatment.TREATED,
        fur_treatment_detail_ru="Стрижка",
        trim_material_ru="Кожа",
    )
    build_photo(product)
    return product


def page_text(client, product) -> str:
    return client.get(product_url(product)).content.decode()


def test_product_page_shows_every_photo(client, product):
    html = page_text(client, product)
    assert all(photo.alt_text_ru in html for photo in product.photos.all())
    assert html.count("<picture") == product.photos.count()


@pytest.mark.parametrize(
    "field",
    [
        "name_ru",
        "description_ru",
        "fur_species_ru",
        "fur_origin_country_ru",
        "fur_treatment_detail_ru",
        "shell_material_ru",
        "lining_material_ru",
        "trim_material_ru",
        "care_instructions_ru",
    ],
)
def test_product_page_shows_each_text(client, product, field):
    assert getattr(product, field) in page_text(client, product)


def test_product_page_shows_the_fur_treatment(client, product):
    assert "Обработанный мех" in page_text(client, product)


def test_product_page_shows_the_price(client, product):
    assert "125 000 ₽" in page_text(client, product)


def test_breadcrumb_and_back_link_use_the_primary_category(client, product, coats):
    sale = build_category(name_ru="Распродажа")
    add_to_category(product, sale, position=1)
    main = page_text(client, product).split("<main", 1)[1].split("</main>", 1)[0]
    coats_url = reverse("catalog:category", kwargs={"slug": coats.slug_ru})
    sale_url = reverse("catalog:category", kwargs={"slug": sale.slug_ru})
    assert main.count(f'href="{coats_url}"') == 2
    assert f'href="{sale_url}"' not in main


def test_an_unpublished_product_is_not_found_with_a_link_home(client):
    draft = build_product()
    response = client.get(product_url(draft))
    assert response.status_code == 404
    assert f'href="{reverse("catalog:home")}"' in response.content.decode()
