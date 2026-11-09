"""One test per validation rule in contracts/catalog-import.md."""

import copy

import pytest

from catalog_import.row_validation import validate_catalog
from catalog_import.workbook_reader import SheetRow
from tests.fixtures.build_sample_catalog import (
    CATEGORIES,
    COLORS,
    PRODUCT_TYPES,
    SIZE_GUIDE_ROWS,
    SIZE_GUIDES,
    product,
    write_photos,
)

VALID_PRODUCT = product("coat", "Шуба")


@pytest.fixture
def photos_dir(tmp_path):
    write_photos(tmp_path, ["coat.jpg"])
    return tmp_path


def valid_sheets() -> dict[str, list[dict]]:
    return {
        "Categories": copy.deepcopy(CATEGORIES),
        "SizeGuides": copy.deepcopy(SIZE_GUIDES),
        "SizeGuideRows": copy.deepcopy(SIZE_GUIDE_ROWS),
        "ProductTypes": copy.deepcopy(PRODUCT_TYPES),
        "Products": [dict(VALID_PRODUCT)],
        "Colors": [dict(COLORS[0], product_key="coat")],
        "Variants": [
            {
                "product_key": "coat",
                "color_key": "natural",
                "size": "m",
                "price_rub": 1000,
                "stock": 1,
            },
        ],
        "Photos": [
            {
                "product_key": "coat",
                "color_key": "",
                "file": "coat.jpg",
                "position": 0,
                "alt_ru": "Шуба спереди",
                "alt_en": "",
            },
        ],
    }


def as_sheet_rows(sheets: dict[str, list[dict]]) -> dict[str, list[SheetRow]]:
    return {
        name: [SheetRow(number=index + 2, values=row) for index, row in enumerate(rows)]
        for name, rows in sheets.items()
    }


def problems_for(sheets, photos_dir) -> list[tuple[str, int, str, str]]:
    catalog = validate_catalog(as_sheet_rows(sheets), photos_dir)
    return [(p.sheet, p.row, p.column, p.message) for p in catalog.problems]


def only_problem(sheets, photos_dir) -> tuple[str, int, str, str]:
    problems = problems_for(sheets, photos_dir)
    assert len(problems) == 1, problems
    return problems[0]


def test_valid_sheets_have_no_problems(photos_dir):
    assert problems_for(valid_sheets(), photos_dir) == []


def test_a_missing_required_value_is_reported(photos_dir):
    sheets = valid_sheets()
    sheets["Products"][0]["description_ru"] = ""
    sheet, row, column, message = only_problem(sheets, photos_dir)
    assert (sheet, row, column) == ("Products", 2, "description_ru")
    assert "Обязательное поле" in message


def test_an_unknown_key_is_reported(photos_dir):
    sheets = valid_sheets()
    sheets["Products"][0]["type_key"] = "jackets"
    sheet, row, column, message = only_problem(sheets, photos_dir)
    assert (sheet, row, column) == ("Products", 2, "type_key")
    assert "Неизвестный ключ «jackets»" in message


def test_an_unknown_size_is_reported(photos_dir):
    sheets = valid_sheets()
    sheets["Variants"][0]["size"] = "zz"
    sheet, row, column, message = only_problem(sheets, photos_dir)
    assert (sheet, row, column) == ("Variants", 2, "size")
    assert "размер «zz»" in message


@pytest.mark.parametrize("price", [0, -5, "дорого", 99.5])
def test_a_price_that_is_not_a_positive_whole_number_is_reported(photos_dir, price):
    sheets = valid_sheets()
    sheets["Variants"][0]["price_rub"] = price
    sheet, row, column, message = only_problem(sheets, photos_dir)
    assert (sheet, row, column) == ("Variants", 2, "price_rub")
    assert "больше нуля" in message


def test_a_negative_stock_is_reported(photos_dir):
    sheets = valid_sheets()
    sheets["Variants"][0]["stock"] = -1
    sheet, row, column, message = only_problem(sheets, photos_dir)
    assert (sheet, row, column) == ("Variants", 2, "stock")
    assert "не меньше нуля" in message


def test_one_size_mixed_with_letter_sizes_is_reported(photos_dir):
    sheets = valid_sheets()
    sheets["Variants"].append(dict(sheets["Variants"][0], size="one"))
    sheet, row, column, message = only_problem(sheets, photos_dir)
    assert (sheet, row, column) == ("Variants", 3, "size")
    assert "one" in message


def test_a_duplicate_key_is_reported(photos_dir):
    sheets = valid_sheets()
    sheets["Categories"].append(dict(CATEGORIES[0], name_ru="Дубль"))
    sheet, row, column, message = only_problem(sheets, photos_dir)
    assert (sheet, row, column) == ("Categories", 5, "category_key")
    assert "Повторяющийся ключ «coats»" in message


def test_a_treated_fur_without_detail_is_reported(photos_dir):
    sheets = valid_sheets()
    sheets["Products"][0]["fur_treatment"] = "treated"
    sheet, row, column, message = only_problem(sheets, photos_dir)
    assert (sheet, row, column) == ("Products", 2, "fur_treatment_detail_ru")
    assert "обработ" in message


def test_a_missing_photo_file_is_reported(photos_dir):
    sheets = valid_sheets()
    sheets["Photos"][0]["file"] = "lost.jpg"
    sheet, row, column, message = only_problem(sheets, photos_dir)
    assert (sheet, row, column) == ("Photos", 2, "file")
    assert "lost.jpg" in message


def test_a_bad_publish_value_is_reported(photos_dir):
    sheets = valid_sheets()
    sheets["Products"][0]["publish"] = "maybe"
    sheet, row, column, message = only_problem(sheets, photos_dir)
    assert (sheet, row, column) == ("Products", 2, "publish")
    assert "yes или no" in message


def test_prices_are_converted_to_kopecks(photos_dir):
    catalog = validate_catalog(as_sheet_rows(valid_sheets()), photos_dir)
    assert catalog.variants[0].price_kopecks == 100_000


def test_a_product_with_a_problem_is_marked_for_drafting(photos_dir):
    sheets = valid_sheets()
    sheets["Variants"][0]["stock"] = -1
    catalog = validate_catalog(as_sheet_rows(sheets), photos_dir)
    assert catalog.products["coat"].has_problems


def test_a_product_without_a_name_is_skipped(photos_dir):
    sheets = valid_sheets()
    sheets["Products"][0]["name_ru"] = ""
    catalog = validate_catalog(as_sheet_rows(sheets), photos_dir)
    assert "coat" not in catalog.products
