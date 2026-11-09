"""Writes the sample launch workbook used by the import tests and the quickstart.

    uv run python -m tests.fixtures.build_sample_catalog

creates tests/fixtures/sample_catalog.xlsx and generated 2:3 photos in tests/fixtures/photos/.
It holds valid rows plus one example of each problem in contracts/catalog-import.md.
"""

from pathlib import Path

from openpyxl import Workbook
from PIL import Image

from catalog_import.workbook_reader import SHEET_COLUMNS

FIXTURES = Path(__file__).resolve().parent


CATEGORIES = [
    {"category_key": "coats", "name_ru": "Шубы", "name_en": "Fur coats", "position": 0},
    {"category_key": "hats", "name_ru": "Шапки", "name_en": "Hats", "position": 1},
    {"category_key": "sale", "name_ru": "Распродажа", "name_en": "", "position": 2},
]

SIZE_GUIDES = [
    {
        "guide_key": "coats-2026",
        "internal_name": "Длинные шубы 2026",
        "how_to_measure_ru": "Обхват груди измеряйте по самой выступающей точке.",
        "how_to_measure_en": "Measure the chest at its fullest point.",
    }
]

SIZE_GUIDE_ROWS = [
    {"guide_key": "coats-2026", "size": size, "chest_cm": 84 + 4 * step, "waist_cm": 66 + 4 * step,
     "hips_cm": 92 + 4 * step, "sleeve_cm": 60.5 + step, "length_cm": 110 + 2 * step}
    for step, size in enumerate(["s", "m", "l"])
]  # fmt: skip

PRODUCT_TYPES = [
    {"type_key": "long-coat", "name_ru": "Длинные шубы", "name_en": "Long coats",
     "guide_key": "coats-2026"},
    {"type_key": "hat", "name_ru": "Шапки", "name_en": "Hats", "guide_key": ""},
]  # fmt: skip


def product(key: str, name_ru: str, **changes) -> dict:
    row = {
        "product_key": key,
        "name_ru": name_ru,
        "name_en": "",
        "description_ru": "Шуба свободного кроя с отложным воротником.",
        "description_en": "A loose-fitting coat with a turn-down collar.",
        "care_ru": "Только профессиональная чистка меха.",
        "care_en": "Professional fur cleaning only.",
        "fur_species_ru": "Норка",
        "fur_species_en": "Mink",
        "fur_origin_ru": "Дания",
        "fur_origin_en": "Denmark",
        "fur_treatment": "natural",
        "fur_treatment_detail_ru": "",
        "fur_treatment_detail_en": "",
        "shell_ru": "Натуральный мех",
        "shell_en": "Natural fur",
        "lining_ru": "Шёлк",
        "lining_en": "Silk",
        "trim_ru": "",
        "trim_en": "",
        "type_key": "long-coat",
        "guide_key": "",
        "categories": "coats",
        "publish": "yes",
    }
    return row | changes


PRODUCTS = [
    product("mink-classic", "Шуба из норки «Классика»", name_en="Classic mink coat",
            categories="coats, sale"),
    product("sable-long", "Длинная шуба из соболя", name_en="Long sable coat",
            fur_species_ru="Соболь", fur_treatment="treated", fur_treatment_detail_ru="Стрижка"),
    product("fox-hat", "Шапка из лисы", name_en="Fox hat", type_key="hat", categories="hats",
            fur_species_ru="Лиса"),
    product("draft-coat", "Шуба в работе", publish="no"),
    product("treated-no-detail", "Шуба с обработкой", fur_treatment="treated"),
    product("bad-variants", "Шуба с ошибками в вариантах"),
    product("mixed-sizes", "Шуба со смешанными размерами"),
    product("missing-photo", "Шуба без файла фото"),
    product("bad-publish", "Шуба с неверным publish", publish="maybe"),
    product("unknown-category", "Шуба в неизвестной категории", categories="coats, furs"),
    product("no-photos", "Шуба без фотографий"),
    product("mink-classic", "Повтор ключа"),
    product("", "Шуба без ключа"),
    product("no-name", ""),
]  # fmt: skip

COLORS = [
    {"product_key": key, "color_key": "natural", "name_ru": "Натуральный", "name_en": "Natural",
     "position": 0}
    for key in ["mink-classic", "sable-long", "fox-hat", "draft-coat", "treated-no-detail",
                "bad-variants", "mixed-sizes", "missing-photo", "bad-publish",
                "unknown-category", "no-photos"]
] + [
    {"product_key": "mink-classic", "color_key": "graphite", "name_ru": "Графит",
     "name_en": "Graphite", "position": 1},
    {"product_key": "bad-variants", "color_key": "natural", "name_ru": "Повтор цвета",
     "name_en": "", "position": 2},
]  # fmt: skip

VARIANTS = [
    {"product_key": "mink-classic", "color_key": "natural", "size": "s", "price_rub": 180000, "stock": 2},
    {"product_key": "mink-classic", "color_key": "natural", "size": "m", "price_rub": 185000, "stock": 0},
    {"product_key": "mink-classic", "color_key": "graphite", "size": "m", "price_rub": 185000, "stock": 1},
    {"product_key": "sable-long", "color_key": "natural", "size": "l", "price_rub": 950000, "stock": 1},
    {"product_key": "fox-hat", "color_key": "natural", "size": "one", "price_rub": 35000, "stock": 4},
    {"product_key": "draft-coat", "color_key": "natural", "size": "m", "price_rub": 120000, "stock": 1},
    {"product_key": "treated-no-detail", "color_key": "natural", "size": "m", "price_rub": 120000, "stock": 1},
    {"product_key": "bad-variants", "color_key": "natural", "size": "zz", "price_rub": 120000, "stock": 1},
    {"product_key": "bad-variants", "color_key": "natural", "size": "m", "price_rub": 0, "stock": 1},
    {"product_key": "bad-variants", "color_key": "natural", "size": "l", "price_rub": 120000, "stock": -1},
    {"product_key": "bad-variants", "color_key": "pink", "size": "s", "price_rub": 120000, "stock": 1},
    {"product_key": "mixed-sizes", "color_key": "natural", "size": "one", "price_rub": 120000, "stock": 1},
    {"product_key": "mixed-sizes", "color_key": "natural", "size": "m", "price_rub": 120000, "stock": 1},
    {"product_key": "missing-photo", "color_key": "natural", "size": "m", "price_rub": 120000, "stock": 1},
    {"product_key": "bad-publish", "color_key": "natural", "size": "m", "price_rub": 120000, "stock": 1},
    {"product_key": "unknown-category", "color_key": "natural", "size": "m", "price_rub": 120000, "stock": 1},
    {"product_key": "no-photos", "color_key": "natural", "size": "m", "price_rub": 120000, "stock": 1},
]  # fmt: skip

PHOTO_PRODUCTS = ["mink-classic", "sable-long", "fox-hat", "draft-coat", "treated-no-detail",
                  "bad-variants", "mixed-sizes", "bad-publish", "unknown-category"]  # fmt: skip

PHOTOS: list[dict] = [
    {"product_key": key, "color_key": "", "file": f"{key}.jpg", "position": 0,
     "alt_ru": "Фото товара спереди", "alt_en": "Front view"}
    for key in PHOTO_PRODUCTS
] + [
    {"product_key": "mink-classic", "color_key": "graphite", "file": "mink-classic-graphite.jpg",
     "position": 1, "alt_ru": "Графит, вид спереди", "alt_en": ""},
    {"product_key": "missing-photo", "color_key": "", "file": "does-not-exist.jpg", "position": 0,
     "alt_ru": "Нет файла", "alt_en": ""},
]  # fmt: skip

SHEET_ROWS: dict[str, list[dict]] = {
    "Categories": CATEGORIES,
    "SizeGuides": SIZE_GUIDES,
    "SizeGuideRows": SIZE_GUIDE_ROWS,
    "ProductTypes": PRODUCT_TYPES,
    "Products": PRODUCTS,
    "Colors": COLORS,
    "Variants": VARIANTS,
    "Photos": PHOTOS,
}


def write_workbook(path: Path, sheet_rows: dict[str, list[dict]] = SHEET_ROWS) -> Path:
    workbook = Workbook()
    workbook.remove(workbook.active)
    for sheet_name, columns in SHEET_COLUMNS.items():
        sheet = workbook.create_sheet(sheet_name)
        sheet.append(columns)
        for row in sheet_rows.get(sheet_name, []):
            sheet.append([row.get(column, "") for column in columns])
    workbook.save(path)
    return path


def write_photos(directory: Path, file_names: list[str], width: int = 720) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name in file_names:
        Image.new("RGB", (width, width * 3 // 2), (200, 200, 200)).save(directory / name, "JPEG")


def build_sample_catalog(directory: Path = FIXTURES) -> tuple[Path, Path]:
    """Writes the workbook and its photos into `directory`; returns (workbook, photos folder)."""
    photos = directory / "photos"
    existing_files = [row["file"] for row in PHOTOS if row["file"] != "does-not-exist.jpg"]
    write_photos(photos, existing_files)
    return write_workbook(directory / "sample_catalog.xlsx"), photos


if __name__ == "__main__":
    workbook, photos = build_sample_catalog()
    print(f"Wrote {workbook} and photos in {photos}")
