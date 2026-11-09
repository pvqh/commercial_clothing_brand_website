"""A launch-sized workbook for the SC-008 timing check: 200 products, 3 full-size photos each.

uv run python -m tests.fixtures.build_catalog_200 <folder>
"""

import sys
from pathlib import Path

from tests.fixtures.build_sample_catalog import (
    CATEGORIES,
    PRODUCT_TYPES,
    SIZE_GUIDE_ROWS,
    SIZE_GUIDES,
    product,
    write_photos,
    write_workbook,
)

PRODUCT_COUNT = 200
PHOTOS_PER_PRODUCT = 3
COLORS = [("natural", "Натуральный", "Natural"), ("graphite", "Графит", "Graphite")]
SIZES = ["s", "m", "l", "xl"]
FULL_PHOTO_WIDTH = 1440


def product_rows(number: int) -> dict[str, list[dict]]:
    key = f"coat-{number:03d}"
    colors = [
        {"product_key": key, "color_key": color_key, "name_ru": name_ru, "name_en": name_en,
         "position": position}
        for position, (color_key, name_ru, name_en) in enumerate(COLORS)
    ]  # fmt: skip
    variants = [
        {"product_key": key, "color_key": color_key, "size": size,
         "price_rub": 100_000 + 1_000 * number, "stock": (number + index) % 4}
        for color_key, *_ in COLORS
        for index, size in enumerate(SIZES)
    ]  # fmt: skip
    photos = [
        {"product_key": key, "color_key": "", "file": f"{key}-{position}.jpg",
         "position": position, "alt_ru": f"Шуба {number}, фото {position + 1}", "alt_en": ""}
        for position in range(PHOTOS_PER_PRODUCT)
    ]  # fmt: skip
    return {
        "Products": [product(key, f"Шуба из норки №{number}", name_en=f"Mink coat {number}")],
        "Colors": colors,
        "Variants": variants,
        "Photos": photos,
    }


def build_catalog_200(directory: Path) -> tuple[Path, Path]:
    sheets: dict[str, list[dict]] = {
        "Categories": CATEGORIES,
        "SizeGuides": SIZE_GUIDES,
        "SizeGuideRows": SIZE_GUIDE_ROWS,
        "ProductTypes": PRODUCT_TYPES,
        "Products": [],
        "Colors": [],
        "Variants": [],
        "Photos": [],
    }
    for number in range(1, PRODUCT_COUNT + 1):
        for sheet, rows in product_rows(number).items():
            sheets[sheet] += rows
    photos = directory / "photos"
    write_photos(photos, [row["file"] for row in sheets["Photos"]], width=FULL_PHOTO_WIDTH)
    return write_workbook(directory / "catalog_200.xlsx", sheets), photos


if __name__ == "__main__":
    workbook, photo_folder = build_catalog_200(Path(sys.argv[1]))
    print(f"Wrote {workbook} and photos in {photo_folder}")
