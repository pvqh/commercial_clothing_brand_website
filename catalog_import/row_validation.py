"""Validation of every workbook row against contracts/catalog-import.md.

Each sheet has one validator. Problems are written to a shared log in Russian with their sheet,
row and column; valid data is returned as typed rows. A product with a problem in any of its own
rows is kept but marked `has_problems`, so it is saved as an unpublished draft (FR-031).
"""

from dataclasses import dataclass, field
from pathlib import Path

from django.utils.translation import gettext as _

from catalog.models import FurTreatment, Size
from catalog.models.size_guide import MEASUREMENT_FIELDS

from .problems import ProblemLog
from .row_fields import RowFields
from .validated_rows import (
    CategoryRow,
    ColorRow,
    PhotoRow,
    ProductRow,
    ProductTypeRow,
    SizeGuideData,
    SizeGuideRowData,
    ValidatedCatalog,
    VariantRow,
)
from .workbook_reader import SheetRow

PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
SIZE_CODES = {size.code: size for size in Size}
LETTER_SIZE_CODES = {size.code: size for size in Size.letter_sizes()}
TREATMENTS = {treatment.value: treatment for treatment in FurTreatment}
YES_NO = {"yes": True, "no": False}

# Products column → (model field, maximum length or None, required)
PRODUCT_TEXT_COLUMNS = {
    "name_ru": ("name_ru", 150, True),
    "name_en": ("name_en", 150, False),
    "description_ru": ("description_ru", None, True),
    "description_en": ("description_en", None, False),
    "care_ru": ("care_instructions_ru", None, True),
    "care_en": ("care_instructions_en", None, False),
    "fur_species_ru": ("fur_species_ru", 100, True),
    "fur_species_en": ("fur_species_en", 100, False),
    "fur_origin_ru": ("fur_origin_country_ru", 100, True),
    "fur_origin_en": ("fur_origin_country_en", 100, False),
    "fur_treatment_detail_ru": ("fur_treatment_detail_ru", 200, False),
    "fur_treatment_detail_en": ("fur_treatment_detail_en", 200, False),
    "shell_ru": ("shell_material_ru", 200, True),
    "shell_en": ("shell_material_en", 200, False),
    "lining_ru": ("lining_material_ru", 200, True),
    "lining_en": ("lining_material_en", 200, False),
    "trim_ru": ("trim_material_ru", 200, False),
    "trim_en": ("trim_material_en", 200, False),
}


@dataclass
class KeyRegistry:
    """Keys of one sheet: those accepted and those whose rows were rejected."""

    sheet: str
    accepted: set[str] = field(default_factory=set)
    rejected: set[str] = field(default_factory=set)

    def seen(self, key: str) -> bool:
        return key in self.accepted or key in self.rejected

    def check_reference(self, fields: RowFields, column: str, key: str) -> bool:
        if key in self.accepted:
            return True
        if key in self.rejected:
            message = _("The row with key «%(key)s» on sheet %(sheet)s was rejected.")
            fields.report(column, message % {"key": key, "sheet": self.sheet})
        else:
            fields.report(column, _("Unknown key «%(key)s».") % {"key": key})
        return False


def validate_catalog(sheets: dict[str, list[SheetRow]], photos_dir: Path) -> ValidatedCatalog:
    log = ProblemLog()
    catalog = ValidatedCatalog()
    validator = CatalogValidator(catalog, log, photos_dir)
    validator.validate(sheets)
    catalog.problems = log.problems
    catalog.rejected_row_count = log.rejected_row_count()
    return catalog


class CatalogValidator:
    def __init__(self, catalog: ValidatedCatalog, log: ProblemLog, photos_dir: Path):
        self.catalog = catalog
        self.log = log
        self.photos_dir = photos_dir
        self.categories = KeyRegistry("Categories")
        self.guides = KeyRegistry("SizeGuides")
        self.types = KeyRegistry("ProductTypes")
        self.products = KeyRegistry("Products")
        self.sizes_by_product: dict[str, set[bool]] = {}

    def validate(self, sheets: dict[str, list[SheetRow]]) -> None:
        steps = [
            ("Categories", self.validate_category),
            ("SizeGuides", self.validate_size_guide),
            ("SizeGuideRows", self.validate_size_guide_row),
            ("ProductTypes", self.validate_product_type),
            ("Products", self.validate_product),
            ("Colors", self.validate_color),
            ("Variants", self.validate_variant),
            ("Photos", self.validate_photo),
        ]
        for sheet, validate_row in steps:
            for row in sheets[sheet]:
                validate_row(RowFields(sheet, row, self.log))

    def unique_key(self, fields: RowFields, column: str, registry: KeyRegistry) -> str:
        key = fields.text(column, required=True)
        if key and registry.seen(key):
            fields.report(column, _("Duplicate key «%(key)s».") % {"key": key})
            return ""
        return key

    def remember(self, fields: RowFields, registry: KeyRegistry, key: str) -> bool:
        if key:
            (registry.accepted if fields.is_valid else registry.rejected).add(key)
        return fields.is_valid and bool(key)

    def validate_category(self, fields: RowFields) -> None:
        key = self.unique_key(fields, "category_key", self.categories)
        row = CategoryRow(
            key=key,
            name_ru=fields.text("name_ru", required=True, max_length=80),
            name_en=fields.text("name_en", max_length=80),
            position=fields.position() or 0,
        )
        if self.remember(fields, self.categories, key):
            self.catalog.categories[key] = row

    def validate_size_guide(self, fields: RowFields) -> None:
        key = self.unique_key(fields, "guide_key", self.guides)
        guide = SizeGuideData(
            key=key,
            internal_name=fields.text("internal_name", required=True, max_length=100),
            how_to_measure_ru=fields.text("how_to_measure_ru", required=True),
            how_to_measure_en=fields.text("how_to_measure_en"),
        )
        if self.remember(fields, self.guides, key):
            self.catalog.size_guides[key] = guide

    def validate_size_guide_row(self, fields: RowFields) -> None:
        guide_key = fields.text("guide_key", required=True)
        if guide_key:
            self.guides.check_reference(fields, "guide_key", guide_key)
        message = _("Unknown size «%(value)s»: use xxs … xxxl.")
        size = fields.choice("size", LETTER_SIZE_CODES, message)
        measured = {name: fields.measurement(name) for name in MEASUREMENT_FIELDS}
        measurements = {name: value for name, value in measured.items() if value is not None}
        if fields.is_valid and self.is_new_guide_size(fields, guide_key, size):
            row = SizeGuideRowData(guide_key=guide_key, size=size, measurements=measurements)
            self.catalog.size_guide_rows.append(row)

    def is_new_guide_size(self, fields: RowFields, guide_key: str, size: Size) -> bool:
        taken = any(
            row.guide_key == guide_key and row.size == size for row in self.catalog.size_guide_rows
        )
        if taken:
            fields.report("size", _("This size is already listed in the size guide."))
        return not taken

    def validate_product_type(self, fields: RowFields) -> None:
        key = self.unique_key(fields, "type_key", self.types)
        guide_key = fields.text("guide_key")
        if guide_key:
            self.guides.check_reference(fields, "guide_key", guide_key)
        product_type = ProductTypeRow(
            key=key,
            name_ru=fields.text("name_ru", required=True, max_length=80),
            name_en=fields.text("name_en", max_length=80),
            guide_key=guide_key,
        )
        if self.remember(fields, self.types, key):
            self.catalog.product_types[key] = product_type

    def validate_product(self, fields: RowFields) -> None:
        key = self.unique_key(fields, "product_key", self.products)
        texts = product_texts(fields)
        if not key or not texts["name_ru"]:
            if key:
                self.products.rejected.add(key)
            return
        product = ProductRow(
            row_number=fields.row.number,
            key=key,
            fields=texts | {"fur_treatment": product_treatment(fields, texts)},
            type_key=self.product_type_key(fields),
            guide_key=self.product_guide_key(fields),
            category_keys=self.product_category_keys(fields),
            publish=bool(fields.choice("publish", YES_NO, _("Use yes or no."))),
        )
        product.has_problems = not fields.is_valid
        self.products.accepted.add(key)
        self.catalog.products[key] = product

    def product_type_key(self, fields: RowFields) -> str:
        key = fields.text("type_key", required=True)
        return key if key and self.types.check_reference(fields, "type_key", key) else ""

    def product_guide_key(self, fields: RowFields) -> str:
        key = fields.text("guide_key")
        return key if key and self.guides.check_reference(fields, "guide_key", key) else ""

    def product_category_keys(self, fields: RowFields) -> list[str]:
        listed = [key.strip() for key in fields.text("categories", required=True).split(",")]
        return [
            key
            for key in dict.fromkeys(listed)
            if key and self.categories.check_reference(fields, "categories", key)
        ]

    def product_for(self, fields: RowFields) -> ProductRow | None:
        key = fields.text("product_key", required=True)
        if key and self.products.check_reference(fields, "product_key", key):
            return self.catalog.products[key]
        return None

    def mark_problems(self, fields: RowFields, product: ProductRow | None) -> bool:
        if product is not None and not fields.is_valid:
            product.has_problems = True
        return product is not None and fields.is_valid

    def validate_color(self, fields: RowFields) -> None:
        product = self.product_for(fields)
        color_key = fields.text("color_key", required=True)
        color = ColorRow(
            product_key=product.key if product else "",
            key=color_key,
            name_ru=fields.text("name_ru", required=True, max_length=60),
            name_en=fields.text("name_en", max_length=60),
            position=fields.position() or 0,
        )
        if product and color_key:
            self.check_color_is_new(fields, color)
        if self.mark_problems(fields, product):
            self.catalog.colors[(color.product_key, color.key)] = color

    def check_color_is_new(self, fields: RowFields, color: ColorRow) -> None:
        if (color.product_key, color.key) in self.catalog.colors:
            fields.report("color_key", _("Duplicate key «%(key)s».") % {"key": color.key})
            return
        positions = {
            existing.position
            for existing in self.catalog.colors.values()
            if existing.product_key == color.product_key
        }
        if color.position in positions:
            fields.report("position", _("This position is already used by another color."))

    def color_for(self, fields: RowFields, product: ProductRow | None) -> str:
        color_key = fields.text("color_key", required=product is not None)
        if product and color_key and (product.key, color_key) not in self.catalog.colors:
            fields.report("color_key", _("Unknown key «%(key)s».") % {"key": color_key})
        return color_key

    def validate_variant(self, fields: RowFields) -> None:
        product = self.product_for(fields)
        color_key = self.color_for(fields, product)
        size = fields.choice(
            "size", SIZE_CODES, _("Unknown size «%(value)s»: use xxs … xxxl or one.")
        )
        price_rub = fields.whole_number(
            "price_rub", 1, _("The price must be a whole number of rubles greater than zero.")
        )
        stock = fields.whole_number(
            "stock", 0, _("The stock must be a whole number not less than zero.")
        )
        if product and size is not None and fields.is_valid:
            self.check_variant_size(fields, product.key, color_key, size)
        valid = self.mark_problems(fields, product)
        if valid and product and size is not None and price_rub and stock is not None:
            self.catalog.variants.append(
                VariantRow(product.key, color_key, size, price_rub * 100, stock)
            )

    def check_variant_size(self, fields: RowFields, product_key: str, color_key: str, size: Size):
        if any(
            v.product_key == product_key and v.color_key == color_key and v.size == size
            for v in self.catalog.variants
        ):
            fields.report("size", _("This size is already listed for this color."))
            return
        kinds = self.sizes_by_product.setdefault(product_key, set())
        is_one_size = size == Size.ONE
        if kinds and is_one_size not in kinds:
            fields.report("size", _("A product cannot mix the size one with letter sizes."))
            return
        kinds.add(is_one_size)

    def validate_photo(self, fields: RowFields) -> None:
        product = self.product_for(fields)
        color_key = fields.text("color_key")
        if product and color_key and (product.key, color_key) not in self.catalog.colors:
            fields.report("color_key", _("Unknown key «%(key)s».") % {"key": color_key})
        photo_file = self.photo_file(fields)
        photo = PhotoRow(
            product_key=product.key if product else "",
            color_key=color_key,
            file=photo_file,
            position=fields.position() or 0,
            alt_ru=fields.text("alt_ru", required=True, max_length=250),
            alt_en=fields.text("alt_en", max_length=250),
        )
        if self.mark_problems(fields, product):
            self.catalog.photos.append(photo)

    def photo_file(self, fields: RowFields) -> Path:
        name = fields.text("file", required=True)
        path = self.photos_dir / name
        if not name:
            return path
        if path.suffix.lower() not in PHOTO_EXTENSIONS:
            fields.report("file", _("Photos must be JPEG, PNG or WebP files."))
        elif not path.is_file():
            message = _("File «%(file)s» was not found in the photos folder.")
            fields.report("file", message % {"file": name})
        return path


def product_texts(fields: RowFields) -> dict[str, str]:
    return {
        field_name: fields.text(column, required=required, max_length=max_length)
        for column, (field_name, max_length, required) in PRODUCT_TEXT_COLUMNS.items()
    }


def product_treatment(fields: RowFields, texts: dict[str, str]) -> str:
    message = _("Unknown value «%(value)s»: use natural, dyed or treated.")
    treatment = fields.choice("fur_treatment", TREATMENTS, message)
    if treatment == FurTreatment.TREATED and not texts["fur_treatment_detail_ru"]:
        fields.report(
            "fur_treatment_detail_ru", _("Describe the treatment when the fur is treated.")
        )
    return treatment or FurTreatment.NATURAL
