"""Category listings: published products with the price and stock facts their cards need (R13)."""

from django.db.models import (
    BooleanField,
    Case,
    F,
    Max,
    Min,
    Prefetch,
    Q,
    QuerySet,
    Value,
    When,
)
from django.db.models.functions import Coalesce

from catalog.models import Category, Product, ProductPhoto, Size, Variant

from .listing_filters import ListingFilters, Sort

PRICE = "colors__variants__price_kopecks"
IN_STOCK = Q(colors__variants__stock__gt=0)
NEWEST_FIRST = ("-first_published_at", "-id")


def published_listing(category: Category) -> QuerySet[Product]:
    return filtered_listing(category, ListingFilters())


def filtered_listing(category: Category, filters: ListingFilters) -> QuerySet[Product]:
    """Products matching the filters, each priced by its cheapest matching in-stock variant.

    Size and price apply to the same variant. While any filter is active, products without a
    matching in-stock variant (including sold-out ones) are left out (FR-007, FR-008, R13).
    """
    products = Product.objects.filter(is_published=True, category_memberships__category=category)
    products = with_card_prices(products, matching_variant(filters))
    if filters.is_active:
        products = products.filter(price_low_in_stock__isnull=False)  # type: ignore[misc]
    return with_listing_photo(products).order_by(*ordering(filters.sort))


def matching_variant(filters: ListingFilters) -> Q:
    match = IN_STOCK
    if filters.sizes:
        match &= Q(colors__variants__size__in=filters.sizes)
    if filters.price_min is not None:
        match &= Q(colors__variants__price_kopecks__gte=filters.price_min * 100)
    if filters.price_max is not None:
        match &= Q(colors__variants__price_kopecks__lte=filters.price_max * 100)
    return match


def with_card_prices(products: QuerySet[Product], in_stock_match: Q = IN_STOCK) -> QuerySet:
    """Adds `card_price`, `card_price_is_from` and `card_sold_out` to every product."""
    return products.annotate(
        price_low_in_stock=Min(PRICE, filter=in_stock_match),
        price_high_in_stock=Max(PRICE, filter=in_stock_match),
        price_low=Min(PRICE),
        price_high=Max(PRICE),
    ).annotate(
        card_price=Coalesce("price_low_in_stock", "price_low"),
        card_sold_out=Case(
            When(price_low_in_stock__isnull=True, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        ),
        card_price_is_from=Case(
            When(price_low_in_stock__lt=F("price_high_in_stock"), then=Value(True)),
            When(price_low_in_stock__isnull=True, price_low__lt=F("price_high"), then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        ),
    )


def ordering(sort: Sort) -> tuple:
    """Newest first by default; price sorts put sold-out products last (FR-012, FR-013)."""
    if sort == Sort.PRICE_ASC:
        return ("card_sold_out", "card_price", *NEWEST_FIRST)
    if sort == Sort.PRICE_DESC:
        return ("card_sold_out", "-card_price", *NEWEST_FIRST)
    return NEWEST_FIRST


def with_listing_photo(products: QuerySet[Product]) -> QuerySet[Product]:
    """Prefetches photos in gallery order; the first one is the listing photo."""
    ordered_photos = ProductPhoto.objects.order_by("position", "id")
    return products.prefetch_related(
        Prefetch("photos", queryset=ordered_photos, to_attr="ordered_photos")
    )


def offered_sizes(category: Category) -> list[Size]:
    """Sizes that appear among the category's published products, in scale order (FR-006)."""
    variants = Variant.objects.filter(
        color__product__is_published=True,
        color__product__category_memberships__category=category,
    )
    return [
        Size(size) for size in variants.values_list("size", flat=True).distinct().order_by("size")
    ]
