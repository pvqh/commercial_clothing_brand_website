import csv
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.management import call_command
from django.core.management.base import CommandError
from openpyxl import load_workbook

from catalog.models import Category, Color, Product, ProductPhoto, SizeGuide, Variant
from catalog_import.models import CatalogImport
from tests.fixtures.build_sample_catalog import build_sample_catalog

pytestmark = pytest.mark.django_db(transaction=True)

DRAFTS = {
    "Шуба в работе",
    "Шуба с обработкой",
    "Шуба с ошибками в вариантах",
    "Шуба со смешанными размерами",
    "Шуба без файла фото",
    "Шуба с неверным publish",
    "Шуба в неизвестной категории",
    "Шуба без фотографий",
}


@pytest.fixture
def admin_user():
    return get_user_model().objects.create_superuser("admin", password="a-long-password-1")


@pytest.fixture
def sample(tmp_path):
    return build_sample_catalog(tmp_path)


def run_import(sample, *extra: str) -> None:
    workbook, photos = sample
    call_command(
        "import_catalog", str(workbook), "--photos", str(photos), "--run-by", "admin", *extra
    )


def report_rows(sample) -> list[dict]:
    workbook, _ = sample
    report = workbook.with_name(f"{workbook.stem}-report.csv")
    with report.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def test_valid_categories_are_imported(admin_user, sample):
    run_import(sample)
    assert set(Category.objects.values_list("name_ru", flat=True)) == {
        "Шубы",
        "Шапки",
        "Распродажа",
    }


def test_valid_products_are_published(admin_user, sample):
    run_import(sample)
    published = set(Product.objects.filter(is_published=True).values_list("name_en", flat=True))
    assert published == {"Classic mink coat", "Long sable coat", "Fox hat"}


def test_products_with_problems_are_saved_as_drafts(admin_user, sample):
    run_import(sample)
    drafts = set(Product.objects.filter(is_published=False).values_list("name_ru", flat=True))
    assert drafts == DRAFTS


def test_rows_without_a_key_or_name_are_skipped(admin_user, sample):
    run_import(sample)
    assert not Product.objects.filter(name_ru__in=["Шуба без ключа", "Повтор ключа"]).exists()


def test_colors_variants_and_size_guides_are_imported(admin_user, sample):
    run_import(sample)
    mink = Product.objects.get(name_en="Classic mink coat")
    assert list(mink.colors.values_list("name_ru", flat=True)) == ["Натуральный", "Графит"]
    assert mink.variants.count() == 3
    assert SizeGuide.objects.get().rows.count() == 3


def test_prices_are_stored_in_kopecks(admin_user, sample):
    run_import(sample)
    assert (
        Variant.objects.get(color__product__name_en="Long sable coat").price_kopecks == 95_000_000
    )


def test_the_first_listed_category_is_primary(admin_user, sample):
    run_import(sample)
    mink = Product.objects.get(name_en="Classic mink coat")
    assert mink.primary_category.name_ru == "Шубы"
    assert mink.categories.count() == 2


def test_photos_are_imported_with_renditions(admin_user, sample):
    run_import(sample)
    photo = ProductPhoto.objects.get(product__name_en="Classic mink coat", color__isnull=True)
    assert default_storage.exists(f"photos/{photo.pk}/720.avif")


def test_a_photo_can_belong_to_a_color(admin_user, sample):
    run_import(sample)
    graphite = Color.objects.get(name_ru="Графит")
    assert graphite.photos.count() == 1


def test_categories_that_received_products_are_published(admin_user, sample):
    run_import(sample)
    assert Category.objects.filter(is_published=False).count() == 0


def test_the_report_lists_each_problem_by_sheet_row_and_column(admin_user, sample):
    run_import(sample)
    rows = report_rows(sample)
    assert {"sheet", "row", "column", "problem"} <= set(rows[0])
    assert {"Variants", "Photos", "Products", "Colors"} <= {row["sheet"] for row in rows}


def test_the_import_is_recorded_as_completed(admin_user, sample):
    run_import(sample)
    record = CatalogImport.objects.get()
    assert (record.status, record.products_published, record.products_draft) == ("completed", 3, 8)


def test_a_dry_run_writes_nothing_to_the_catalog(admin_user, sample):
    run_import(sample, "--dry-run")
    assert not Product.objects.exists() and not CatalogImport.objects.exists()


def test_a_dry_run_still_writes_the_report(admin_user, sample):
    run_import(sample, "--dry-run")
    assert report_rows(sample)


def test_a_missing_sheet_stops_the_import(admin_user, sample):
    workbook, _ = sample
    book = load_workbook(workbook)
    del book["Photos"]
    book.save(workbook)
    with pytest.raises(CommandError, match="Photos"):
        run_import(sample)
    assert not Product.objects.exists()


def test_a_missing_column_stops_the_import(admin_user, sample):
    workbook, _ = sample
    book = load_workbook(workbook)
    book["Variants"].delete_cols(5)
    book.save(workbook)
    with pytest.raises(CommandError, match="stock"):
        run_import(sample)


def test_a_second_import_is_refused(admin_user, sample):
    run_import(sample)
    with pytest.raises(CommandError):
        run_import(sample)


def test_an_unexpected_error_rolls_back_and_marks_the_import_failed(admin_user, sample):
    with (
        mock.patch("catalog_import.importer.publish", side_effect=RuntimeError("disk full")),
        pytest.raises(CommandError),
    ):
        run_import(sample)
    assert not Product.objects.exists()
    assert CatalogImport.objects.get().status == "failed"
