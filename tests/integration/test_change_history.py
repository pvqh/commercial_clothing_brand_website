import pytest
from django.core.files.storage import default_storage

from audit.models import ChangeRecord
from catalog.demo_catalog import (
    add_to_category,
    build_category,
    build_color,
    build_photo,
    build_product,
    build_published_product,
    build_variant,
)
from catalog.models import Product, Size
from tests.staff_helpers import change_form_data, create_staff, inline_formset, inline_prefix

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff(client):
    user = create_staff()
    client.force_login(user)
    return user


@pytest.fixture
def product():
    product = build_published_product(build_category(), name_ru="Шуба из норки")
    build_photo(product)
    return product


def resubmit(client, url: str, **changes):
    data = change_form_data(client.get(url)) | changes
    response = client.post(url, data)
    assert response.status_code == 302, response.context and response.context.get("errors")
    return response


def color_url(color) -> str:
    return f"/staff/catalog/color/{color.pk}/change/"


def product_url(product) -> str:
    return f"/staff/catalog/product/{product.pk}/change/"


def test_a_price_change_writes_one_updated_record(client, staff, product):
    color = product.colors.get()
    page = client.get(color_url(color))
    resubmit(
        client, color_url(color), **{f"{inline_prefix(page, 'variant')}-0-price_rub": "130000"}
    )
    record = ChangeRecord.objects.get(entity_type="variant", action="updated")
    assert (record.field_name, record.old_value, record.new_value) == (
        "price_kopecks",
        12_500_000,
        13_000_000,
    )


def test_a_change_record_names_the_staff_member_and_time(client, staff, product):
    resubmit(client, product_url(product), description_ru="Новое описание")
    record = ChangeRecord.objects.get(field_name="description_ru")
    assert record.staff == staff and record.changed_at is not None


def test_one_save_shares_a_change_set(client, staff, product):
    resubmit(
        client, product_url(product), description_ru="Новое", care_instructions_ru="Новый уход"
    )
    change_sets = set(ChangeRecord.objects.values_list("change_set", flat=True))
    assert ChangeRecord.objects.count() == 2 and len(change_sets) == 1


def test_deleting_a_photo_records_a_snapshot_and_keeps_the_file(client, staff, product):
    photo = product.photos.last()
    page = client.get(product_url(product))
    formset = inline_formset(page, "productphoto")
    index = [form.instance.pk for form in formset.forms].index(photo.pk)
    resubmit(client, product_url(product), **{f"{formset.prefix}-{index}-DELETE": "on"})
    record = ChangeRecord.objects.get(entity_type="productphoto", action="deleted")
    assert record.old_value["alt_text_ru"] == photo.alt_text_ru
    assert default_storage.exists(photo.original.name)


def test_creating_a_category_records_a_snapshot(client, staff):
    url = "/staff/catalog/category/add/"
    data = change_form_data(client.get(url)) | {"name_ru": "Жилеты", "position": "3"}
    client.post(url, data)
    record = ChangeRecord.objects.get(entity_type="category", action="created")
    assert record.new_value["name_ru"] == "Жилеты"


def test_bulk_publishing_writes_one_record_per_product(client, staff):
    category = build_category()
    products = []
    for _ in range(2):
        product = build_product()
        add_to_category(product, category)
        build_variant(build_color(product), Size.M)
        build_photo(product)
        products.append(product)
    client.post(
        "/staff/catalog/product/",
        {"action": "publish_selected", "_selected_action": [p.pk for p in products]},
    )
    records = ChangeRecord.objects.filter(field_name="is_published")
    assert records.count() == 2
    assert Product.objects.filter(is_published=True).count() == 2


def test_a_disabled_account_keeps_its_name_on_earlier_changes(client, staff, product):
    resubmit(client, product_url(product), description_ru="Новое описание")
    staff.is_active = False
    staff.save()
    record = ChangeRecord.objects.get(field_name="description_ru")
    assert record.staff.first_name == "Анна"
