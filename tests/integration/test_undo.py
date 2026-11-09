import pytest

from audit.models import ChangeRecord
from audit.recording import new_change_set, record_created, record_deleted, record_update
from audit.undo import UndoRefused, undo
from catalog.demo_catalog import build_category, build_photo, build_product
from catalog.models import Category, ProductPhoto
from tests.staff_helpers import create_staff

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff():
    return create_staff()


def change_name(category: Category, new_name: str, staff) -> ChangeRecord:
    before = Category.objects.get(pk=category.pk)
    category.name_ru = new_name
    category.save()
    return record_update(before, category, staff, new_change_set())[0]


def test_undoing_an_update_restores_the_old_value(staff):
    category = build_category(name_ru="Шубы")
    undo(change_name(category, "Меха", staff), staff)
    category.refresh_from_db()
    assert category.name_ru == "Шубы"


def test_an_undo_is_recorded_and_points_at_the_original(staff):
    record = change_name(build_category(name_ru="Шубы"), "Меха", staff)
    undo_records = undo(record, staff)
    assert [r.undoes_id for r in undo_records] == [record.pk]
    assert undo_records[0].change_set != record.change_set


def test_undo_is_refused_when_the_value_has_changed_since(staff):
    category = build_category(name_ru="Шубы")
    first = change_name(category, "Меха", staff)
    change_name(category, "Пальто", staff)
    with pytest.raises(UndoRefused):
        undo(first, staff)
    category.refresh_from_db()
    assert category.name_ru == "Пальто"


def test_undoing_a_deleted_photo_recreates_it_with_its_original_id(staff):
    photo = build_photo(build_product())
    photo_id = photo.pk
    record = record_deleted(photo, staff, new_change_set())
    photo.delete()
    undo(record, staff)
    assert ProductPhoto.objects.get(pk=photo_id).alt_text_ru == record.old_value["alt_text_ru"]


def test_undoing_a_delete_is_refused_when_its_parent_is_gone(staff):
    product = build_product()
    photo = build_photo(product)
    record = record_deleted(photo, staff, new_change_set())
    product.delete()
    with pytest.raises(UndoRefused):
        undo(record, staff)


def test_undoing_a_created_row_deletes_it_and_records_the_deletion(staff):
    category = build_category()
    record = record_created(category, staff, new_change_set())
    undo_records = undo(record, staff)
    assert not Category.objects.filter(pk=category.pk).exists()
    assert [r.action for r in undo_records] == ["deleted"]


def test_undoing_a_created_product_also_records_its_children(staff):
    product = build_product()
    build_photo(product)
    record = record_created(product, staff, new_change_set())
    undo_records = undo(record, staff)
    assert {r.entity_type for r in undo_records} == {"product", "productphoto"}


def test_undoing_a_created_row_that_is_gone_is_refused(staff):
    category = build_category()
    record = record_created(category, staff, new_change_set())
    category.delete()
    with pytest.raises(UndoRefused):
        undo(record, staff)


def test_an_undo_can_itself_be_undone(staff):
    category = build_category(name_ru="Шубы")
    undo_record = undo(change_name(category, "Меха", staff), staff)[0]
    undo(undo_record, staff)
    category.refresh_from_db()
    assert category.name_ru == "Меха"
