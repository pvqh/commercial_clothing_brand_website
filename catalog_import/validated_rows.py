"""Rows of the workbook after validation, ready to be saved."""

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from catalog.models import Size

from .problems import ImportProblem


@dataclass(frozen=True)
class CategoryRow:
    key: str
    name_ru: str
    name_en: str
    position: int


@dataclass(frozen=True)
class SizeGuideData:
    key: str
    internal_name: str
    how_to_measure_ru: str
    how_to_measure_en: str


@dataclass(frozen=True)
class SizeGuideRowData:
    guide_key: str
    size: Size
    measurements: dict[str, Decimal]


@dataclass(frozen=True)
class ProductTypeRow:
    key: str
    name_ru: str
    name_en: str
    guide_key: str


@dataclass
class ProductRow:
    row_number: int
    key: str
    fields: dict[str, str]
    type_key: str
    guide_key: str
    category_keys: list[str]
    publish: bool
    has_problems: bool = False


@dataclass(frozen=True)
class ColorRow:
    product_key: str
    key: str
    name_ru: str
    name_en: str
    position: int


@dataclass(frozen=True)
class VariantRow:
    product_key: str
    color_key: str
    size: Size
    price_kopecks: int
    stock: int


@dataclass(frozen=True)
class PhotoRow:
    product_key: str
    color_key: str
    file: Path
    position: int
    alt_ru: str
    alt_en: str


@dataclass
class ValidatedCatalog:
    categories: dict[str, CategoryRow] = field(default_factory=dict)
    size_guides: dict[str, SizeGuideData] = field(default_factory=dict)
    size_guide_rows: list[SizeGuideRowData] = field(default_factory=list)
    product_types: dict[str, ProductTypeRow] = field(default_factory=dict)
    products: dict[str, ProductRow] = field(default_factory=dict)
    colors: dict[tuple[str, str], ColorRow] = field(default_factory=dict)
    variants: list[VariantRow] = field(default_factory=list)
    photos: list[PhotoRow] = field(default_factory=list)
    problems: list[ImportProblem] = field(default_factory=list)
    rejected_row_count: int = 0
