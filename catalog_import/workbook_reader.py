"""Reading the launch workbook: every sheet and column in contracts/catalog-import.md."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

SHEET_COLUMNS = {
    "Categories": ["category_key", "name_ru", "name_en", "position"],
    "SizeGuides": ["guide_key", "internal_name", "how_to_measure_ru", "how_to_measure_en"],
    "SizeGuideRows": [
        "guide_key", "size", "chest_cm", "waist_cm", "hips_cm", "sleeve_cm", "length_cm",
    ],
    "ProductTypes": ["type_key", "name_ru", "name_en", "guide_key"],
    "Products": [
        "product_key", "name_ru", "name_en", "description_ru", "description_en", "care_ru",
        "care_en", "fur_species_ru", "fur_species_en", "fur_origin_ru", "fur_origin_en",
        "fur_treatment", "fur_treatment_detail_ru", "fur_treatment_detail_en", "shell_ru",
        "shell_en", "lining_ru", "lining_en", "trim_ru", "trim_en", "type_key", "guide_key",
        "categories", "publish",
    ],
    "Colors": ["product_key", "color_key", "name_ru", "name_en", "position"],
    "Variants": ["product_key", "color_key", "size", "price_rub", "stock"],
    "Photos": ["product_key", "color_key", "file", "position", "alt_ru", "alt_en"],
}  # fmt: skip


class ImportFormatError(Exception):
    """The workbook cannot be imported at all: unreadable, or a sheet or column is missing."""


@dataclass(frozen=True)
class SheetRow:
    number: int
    values: dict[str, Any]


def read_workbook(path: Path) -> dict[str, list[SheetRow]]:
    try:
        workbook = load_workbook(path, read_only=True, data_only=True)
    except Exception as unreadable:
        raise ImportFormatError(
            f"Не удалось открыть файл {path.name}: {unreadable}"
        ) from unreadable
    try:
        return {
            name: read_sheet(workbook, name, columns) for name, columns in SHEET_COLUMNS.items()
        }
    finally:
        workbook.close()


def read_sheet(workbook, sheet_name: str, columns: list[str]) -> list[SheetRow]:
    if sheet_name not in workbook.sheetnames:
        raise ImportFormatError(f"В файле нет листа «{sheet_name}».")
    rows = workbook[sheet_name].iter_rows(values_only=True)
    header = [clean_header(cell) for cell in next(rows, ())]
    missing = [column for column in columns if column not in header]
    if missing:
        raise ImportFormatError(f"На листе «{sheet_name}» нет столбцов: {', '.join(missing)}.")
    return [
        SheetRow(number=number, values=dict(zip(header, cells, strict=False)))
        for number, cells in enumerate(rows, start=2)
        if not is_blank(cells)
    ]


def clean_header(cell: Any) -> str:
    return str(cell).strip() if cell is not None else ""


def is_blank(cells: tuple) -> bool:
    return all(cell is None or str(cell).strip() == "" for cell in cells)
