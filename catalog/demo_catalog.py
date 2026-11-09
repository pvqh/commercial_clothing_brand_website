"""Builders for valid demo records, shared by the tests and the `seed_demo_catalog` command.

Photos are generated grey 2:3 images with the product name drawn on them, so no third-party
images ever enter the repository.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO
from itertools import count

from django.core.files.base import ContentFile
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from catalog.models import (
    Category,
    Color,
    FurTreatment,
    Product,
    ProductCategory,
    ProductPhoto,
    ProductType,
    Size,
    SizeGuide,
    SizeGuideRow,
    Variant,
)
from catalog.services.slugs import slugify_ru

PHOTO_GREY = (205, 205, 205)
TEXT_GREY = (90, 90, 90)
_sequence = count(1)


def build_category(**overrides) -> Category:
    number = next(_sequence)
    fields = {"name_ru": f"Категория {number}", "name_en": f"Category {number}", "position": number}
    fields |= {"is_published": True} | overrides
    return Category.objects.create(**fields)


def build_size_guide(sizes: list[Size] | None = None) -> SizeGuide:
    guide = SizeGuide.objects.create(
        internal_name=f"Guide {next(_sequence)}",
        how_to_measure_ru="Измерьте обхват груди по самой выступающей точке.",
        how_to_measure_en="Measure around the fullest part of the chest.",
    )
    for step, size in enumerate(sizes or Size.letter_sizes()):
        SizeGuideRow.objects.create(size_guide=guide, size=size, **body_measurements(step))
    return guide


def body_measurements(step: int) -> dict[str, Decimal]:
    return {
        "chest_cm": Decimal(80 + 4 * step),
        "waist_cm": Decimal(62 + 4 * step),
        "hips_cm": Decimal(88 + 4 * step),
        "sleeve_cm": Decimal("59.5") + step,
        "length_cm": Decimal(108 + 2 * step),
    }


def build_product_type(size_guide: SizeGuide | None = None) -> ProductType:
    return ProductType.objects.create(
        name_ru="Длинные шубы", name_en="Long coats", size_guide=size_guide or build_size_guide()
    )


def build_product(**overrides) -> Product:
    """An unpublished product with every required text filled in and no categories or variants."""
    fields = {
        "name_ru": f"Шуба {next(_sequence)}",
        "name_en": "Fur coat",
        "description_ru": "Длинная шуба свободного кроя.",
        "description_en": "A long, loose-fitting coat.",
        "care_instructions_ru": "Только профессиональная чистка меха.",
        "care_instructions_en": "Professional fur cleaning only.",
        "fur_species_ru": "Норка",
        "fur_species_en": "Mink",
        "fur_origin_country_ru": "Дания",
        "fur_origin_country_en": "Denmark",
        "fur_treatment": FurTreatment.NATURAL,
        "shell_material_ru": "Натуральный мех",
        "shell_material_en": "Natural fur",
        "lining_material_ru": "Шёлк",
        "lining_material_en": "Silk",
    } | overrides
    if "product_type" not in fields:
        fields["product_type"] = build_product_type()
    return Product.objects.create(**fields)


def add_to_category(product: Product, category: Category, position: int = 0) -> ProductCategory:
    return ProductCategory.objects.create(product=product, category=category, position=position)


def build_color(product: Product, **overrides) -> Color:
    position = overrides.pop("position", product.colors.count())
    fields = {"name_ru": f"Цвет {position + 1}", "name_en": f"Color {position + 1}"} | overrides
    return Color.objects.create(product=product, position=position, **fields)


def build_variant(color: Color, size: Size = Size.M, **overrides) -> Variant:
    fields = {"price_kopecks": 12_500_000, "stock": 3} | overrides
    return Variant.objects.create(color=color, size=size, **fields)


def build_photo(product: Product | None = None, **overrides) -> ProductPhoto:
    product = product or build_product()
    width = overrides.pop("width", 720)
    height = overrides.pop("height", 1080)
    fields = {
        "position": product.photos.count(),
        "alt_text_ru": f"{product.name_ru}, фото",
        "alt_text_en": f"{product.name_en or product.name_ru}, photo",
    } | overrides
    photo = ProductPhoto(product=product, **fields)
    file_name = f"{product.slug_ru}-{photo.position}.jpg"
    photo.original.save(file_name, demo_photo_file(product.name_ru, width, height))
    return photo


def demo_photo_file(label: str, width: int, height: int) -> ContentFile:
    image = Image.new("RGB", (width, height), PHOTO_GREY)
    font = ImageFont.load_default(size=max(16, width // 18))
    draw = ImageDraw.Draw(image)
    latin_label = slugify_ru(label).replace("-", " ").upper()  # the bundled font has no Cyrillic
    draw.text((width / 2, height / 2), latin_label, fill=TEXT_GREY, font=font, anchor="mm")
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=80)
    return ContentFile(buffer.getvalue())


def publish_directly(product: Product, published_at: datetime | None = None) -> Product:
    """Marks a product published without the publish-rule checks, for building test data."""
    product.is_published = True
    product.first_published_at = product.first_published_at or published_at or timezone.now()
    product.save()
    return product


def build_published_product(category: Category, **options) -> Product:
    """A published product in the category with one color, the given sizes and one photo."""
    sizes = options.pop("sizes", [Size.M])
    stock = options.pop("stock", 3)
    price_kopecks = options.pop("price_kopecks", 12_500_000)
    age = options.pop("age", timedelta(0))
    product = build_product(**options)
    add_to_category(product, category)
    color = build_color(product)
    for size in sizes:
        build_variant(color, size, price_kopecks=price_kopecks, stock=stock)
    build_photo(product)
    return publish_directly(product, timezone.now() - age)
