"""Saving a validated workbook as catalog records (one call, inside the import's transaction)."""

from concurrent.futures import ProcessPoolExecutor

from django.core.files import File

from catalog.models import (
    Category,
    Color,
    Product,
    ProductCategory,
    ProductPhoto,
    ProductType,
    SizeGuide,
    SizeGuideRow,
    Variant,
)
from catalog.services.photo_renditions import rendition_job
from catalog.services.rendition_files import write_rendition_files

from .validated_rows import PhotoRow, ProductRow, ValidatedCatalog


class CatalogWriter:
    def __init__(self, catalog: ValidatedCatalog):
        self.catalog = catalog
        self.categories: dict[str, Category] = {}
        self.guides: dict[str, SizeGuide] = {}
        self.types: dict[str, ProductType] = {}
        self.products: dict[str, Product] = {}
        self.colors: dict[tuple[str, str], Color] = {}

    def write(self) -> dict[str, Product]:
        """Creates every record and returns the products by key."""
        self.write_categories()
        self.write_size_guides()
        self.write_product_types()
        self.write_products()
        self.write_colors_and_variants()
        generate_renditions_in_parallel(self.write_photos())
        self.publish_categories_with_products()
        return self.products

    def write_categories(self) -> None:
        for key, row in self.catalog.categories.items():
            self.categories[key] = Category.objects.create(
                name_ru=row.name_ru, name_en=row.name_en, position=row.position
            )

    def write_size_guides(self) -> None:
        for key, row in self.catalog.size_guides.items():
            self.guides[key] = SizeGuide.objects.create(
                internal_name=row.internal_name,
                how_to_measure_ru=row.how_to_measure_ru,
                how_to_measure_en=row.how_to_measure_en,
            )
        for guide_row in self.catalog.size_guide_rows:
            SizeGuideRow.objects.create(
                size_guide=self.guides[guide_row.guide_key],
                size=guide_row.size,
                **guide_row.measurements,
            )

    def write_product_types(self) -> None:
        for key, row in self.catalog.product_types.items():
            self.types[key] = ProductType.objects.create(
                name_ru=row.name_ru, name_en=row.name_en, size_guide=self.guides.get(row.guide_key)
            )

    def write_products(self) -> None:
        for key, row in self.catalog.products.items():
            self.products[key] = self.create_product(row)

    def create_product(self, row: ProductRow) -> Product:
        product = Product.objects.create(
            **row.fields,
            product_type=self.types.get(row.type_key),
            size_guide=self.guides.get(row.guide_key),
        )
        for position, category_key in enumerate(row.category_keys):
            category = self.categories[category_key]
            ProductCategory.objects.create(product=product, category=category, position=position)
        return product

    def write_colors_and_variants(self) -> None:
        for (product_key, color_key), row in self.catalog.colors.items():
            self.colors[(product_key, color_key)] = Color.objects.create(
                product=self.products[product_key],
                name_ru=row.name_ru,
                name_en=row.name_en,
                position=row.position,
            )
        for variant in self.catalog.variants:
            Variant.objects.create(
                color=self.colors[(variant.product_key, variant.color_key)],
                size=variant.size,
                price_kopecks=variant.price_kopecks,
                stock=variant.stock,
            )

    def write_photos(self) -> list[ProductPhoto]:
        return [self.create_photo(row) for row in self.catalog.photos]

    def create_photo(self, row: PhotoRow) -> ProductPhoto:
        photo = ProductPhoto(
            product=self.products[row.product_key],
            color=self.colors.get((row.product_key, row.color_key)),
            position=row.position,
            alt_text_ru=row.alt_ru,
            alt_text_en=row.alt_en,
        )
        with row.file.open("rb") as source:
            photo.original.save(row.file.name, File(source), save=True)
        return photo

    def publish_categories_with_products(self) -> None:
        used = ProductCategory.objects.filter(product__in=self.products.values())
        Category.objects.filter(pk__in=used.values("category_id")).update(is_published=True)


def generate_renditions_in_parallel(photos: list[ProductPhoto]) -> None:
    """Uses every CPU core so a 200-product catalog loads within SC-008's 15 minutes (R12)."""
    if not photos:
        return
    sources, targets, widths = zip(*(rendition_job(photo) for photo in photos), strict=True)
    with ProcessPoolExecutor() as pool:
        list(pool.map(write_rendition_files, sources, targets, widths))
