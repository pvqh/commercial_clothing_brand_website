from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.demo_catalog import (
    add_to_category,
    build_category,
    build_color,
    build_photo,
    build_product,
    build_published_product,
    build_variant,
    publish_directly,
)
from catalog.models import Category, ProductPhoto, Size
from catalog.services.photo_renditions import generate_renditions

COAT_SIZES = [Size.XS, Size.S, Size.M, Size.L, Size.XL]
COAT_COLORS = [("Натуральный", "Natural"), ("Графит", "Graphite"), ("Карамель", "Caramel")]
OUT_OF_STOCK = {(1, Size.S), (1, Size.L), *((2, size) for size in COAT_SIZES)}


class Command(BaseCommand):
    help = "Fills an empty database with a demo catalog for local work and browser tests."

    def handle(self, *args, **options) -> None:
        if Category.objects.exists():
            self.stderr.write("The catalog is not empty; nothing was added.")
            return
        seed_demo_catalog()
        self.stdout.write(self.style.SUCCESS("Demo catalog created: 2 categories, 30 products."))


def seed_demo_catalog() -> None:
    with transaction.atomic():
        coats = build_category(name_ru="Шубы", name_en="Fur coats", position=0)
        accessories = build_category(name_ru="Аксессуары", name_en="Accessories", position=1)
        seed_regular_products(coats, accessories)
        seed_three_color_coat(coats)
        seed_edge_case_products(coats, accessories)
    for photo in ProductPhoto.objects.all():
        generate_renditions(photo)


def seed_regular_products(coats, accessories) -> None:
    for number in range(1, 27):
        build_published_product(
            coats if number <= 24 else accessories,
            name_ru=f"Шуба из норки {number}",
            name_en=f"Mink coat {number}",
            sizes=[Size.S, Size.M, Size.L] if number % 2 else [Size.M, Size.XL],
            price_kopecks=(90_000 + number * 5_000) * 100,
            age=timedelta(days=number),
        )


def seed_three_color_coat(coats) -> None:
    coat = build_product(name_ru="Шуба из норки «Классика»", name_en="Classic mink coat")
    add_to_category(coat, coats)
    build_photo(coat, width=1440, height=2160)
    for position, (name_ru, name_en) in enumerate(COAT_COLORS):
        color = build_color(coat, name_ru=name_ru, name_en=name_en, position=position)
        build_photo(coat, color=color, width=1440, height=2160)
        for size in COAT_SIZES:
            stock = 0 if (position, size) in OUT_OF_STOCK else 2
            price_kopecks = (150_000 + int(size) * 1_000) * 100
            build_variant(color, size, price_kopecks=price_kopecks, stock=stock)
    publish_directly(coat)


def seed_edge_case_products(coats, accessories) -> None:
    build_published_product(
        coats, name_ru="Шуба из соболя", name_en="Sable coat", stock=0, age=timedelta(days=40)
    )
    build_published_product(
        accessories,
        name_ru="Шарф из лисы",
        name_en="Fox scarf",
        sizes=[Size.ONE],
        price_kopecks=3_500_000,
        age=timedelta(days=2),
    )
    draft = build_product(name_ru="Шуба в работе", name_en="Draft coat")
    add_to_category(draft, coats)
