"""Prices and stock of a product's variants, as shown on its page (FR-020–FR-023, R13)."""

from dataclasses import dataclass

from django.db.models import Max, Min, QuerySet

from catalog.models import Color, Product, Size, Variant


@dataclass(frozen=True)
class PriceRange:
    """The lowest and highest price among in-stock variants, or all variants when sold out."""

    low_kopecks: int | None
    high_kopecks: int | None
    sold_out: bool

    @property
    def is_from(self) -> bool:
        return self.low_kopecks != self.high_kopecks

    @property
    def is_known(self) -> bool:
        return self.low_kopecks is not None


@dataclass(frozen=True)
class SizeOption:
    """One size of the selected color, as offered in the size selector."""

    size: Size
    stock: int
    price_kopecks: int

    @property
    def in_stock(self) -> bool:
        return self.stock > 0

    @property
    def code(self) -> str:
        return self.size.code

    @property
    def label(self) -> str:
        return str(self.size.label)


@dataclass(frozen=True)
class ColorState:
    color: Color
    is_out_of_stock: bool


def price_range(product: Product, color: Color | None = None) -> PriceRange:
    """Prices of the whole product, or of one color when `color` is given."""
    variants = color.variants.all() if color else product.variants
    return price_range_of(variants)


def price_range_of(variants: QuerySet[Variant]) -> PriceRange:
    in_stock = variants.filter(stock__gt=0)
    sold_out = not in_stock.exists()
    prices = (variants if sold_out else in_stock).aggregate(
        low=Min("price_kopecks"), high=Max("price_kopecks")
    )
    return PriceRange(low_kopecks=prices["low"], high_kopecks=prices["high"], sold_out=sold_out)


def availability_for(product: Product, color: Color) -> list[SizeOption]:
    """Every size of `color` in scale order, with its stock and exact price (FR-020)."""
    variants = product.variants.filter(color=color).order_by("size")
    return [
        SizeOption(
            size=Size(variant.size), stock=variant.stock, price_kopecks=variant.price_kopecks
        )
        for variant in variants
    ]


def color_states(product: Product) -> list[ColorState]:
    """Colors in position order, each marked out of stock when none of its sizes is (FR-021)."""
    in_stock_color_ids = set(
        product.variants.filter(stock__gt=0).values_list("color_id", flat=True)
    )
    return [
        ColorState(color=color, is_out_of_stock=color.pk not in in_stock_color_ids)
        for color in product.colors.order_by("position")
    ]
