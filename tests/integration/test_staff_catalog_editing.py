from io import BytesIO

import pytest
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from catalog.demo_catalog import (
    add_to_category,
    build_category,
    build_color,
    build_photo,
    build_product,
    build_published_product,
    build_variant,
)
from catalog.models import Category, Product, Size
from tests.staff_helpers import change_form_data, create_staff, inline_formset

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff(client):
    user = create_staff()
    client.force_login(user)
    return user


def product_url(product) -> str:
    return f"/staff/catalog/product/{product.pk}/change/"


def resubmit(client, url: str, files: dict | None = None, **changes):
    data = change_form_data(client.get(url)) | changes | (files or {})
    return client.post(url, data)


def jpeg_upload(name: str = "new.jpg") -> SimpleUploadedFile:
    buffer = BytesIO()
    Image.new("RGB", (720, 1080), (180, 180, 180)).save(buffer, "JPEG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")


def test_renaming_a_product_gives_it_a_new_address_and_redirects_the_old_one(client, staff):
    product = build_published_product(build_category(), name_ru="Шуба из норки")
    old_slug = product.slug_ru
    resubmit(client, product_url(product), name_ru="Шуба из соболя")
    product.refresh_from_db()
    assert product.slug_ru == "shuba-iz-sobolya"
    assert client.get(f"/tovar/{old_slug}/")["Location"] == f"/tovar/{product.slug_ru}/"


def test_renaming_a_category_redirects_its_old_address(client, staff):
    category = build_category(name_ru="Шубы")
    url = f"/staff/catalog/category/{category.pk}/change/"
    resubmit(client, url, name_ru="Меховые шубы")
    category.refresh_from_db()
    assert client.get("/katalog/shuby/")["Location"] == f"/katalog/{category.slug_ru}/"


def test_uploading_a_photo_creates_its_renditions(client, staff):
    product = build_published_product(build_category())
    page = client.get(product_url(product))
    formset = inline_formset(page, "productphoto")
    index = len(formset.forms) - 1
    prefix = f"{formset.prefix}-{index}"
    resubmit(
        client,
        product_url(product),
        files={f"{prefix}-original": jpeg_upload()},
        **{f"{prefix}-alt_text_ru": "Новое фото", f"{prefix}-position": "5"},
    )
    photo = product.photos.get(alt_text_ru="Новое фото")
    assert default_storage.exists(f"photos/{photo.pk}/720.webp")


def test_products_missing_english_are_listed_under_their_filter(client, staff):
    complete = build_product(name_ru="Полная")
    build_color(complete)
    missing = build_product(name_ru="Без перевода", description_en="")
    response = client.get("/staff/catalog/product/?missing_english=yes")
    listed = list(response.context["cl"].result_list)
    assert missing in listed and complete not in listed


def test_publishing_a_product_that_breaks_a_rule_shows_the_rule(client, staff):
    product = build_product()
    response = client.post(
        "/staff/catalog/product/",
        {"action": "publish_selected", "_selected_action": [product.pk]},
        follow=True,
    )
    messages = " ".join(str(message) for message in response.context["messages"])
    assert "категорию" in messages
    assert not Product.objects.get(pk=product.pk).is_published


def test_a_published_change_is_visible_on_the_next_shop_request(client, staff):
    category = build_category()
    product = build_product(name_ru="Новинка")
    add_to_category(product, category)
    build_variant(build_color(product), Size.M)
    build_photo(product)
    client.post(
        "/staff/catalog/product/", {"action": "publish_selected", "_selected_action": [product.pk]}
    )
    assert client.get(f"/tovar/{product.slug_ru}/").status_code == 200


def test_a_category_with_products_cannot_be_deleted(client, staff):
    category = build_category()
    build_published_product(category)
    client.post(f"/staff/catalog/category/{category.pk}/delete/", {"post": "yes"})
    assert Category.objects.filter(pk=category.pk).exists()
