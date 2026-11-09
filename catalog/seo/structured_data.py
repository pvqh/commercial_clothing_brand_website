"""JSON-LD for product pages (contracts/shopper-routes.md "Structured data")."""

import json
from dataclasses import dataclass

from django.conf import settings
from django.utils.safestring import SafeString, mark_safe

from catalog.models import Product
from catalog.services.product_availability import PriceRange

SCHEMA = "https://schema.org"


@dataclass(frozen=True)
class ProductFacts:
    """What the JSON-LD needs to know about a product beyond its own fields."""

    product: Product
    canonical_url: str
    image_urls: list[str]
    prices: PriceRange


def product_json_ld(facts: ProductFacts) -> dict:
    product = facts.product
    return {
        "@context": SCHEMA,
        "@type": "Product",
        "name": product.localized("name"),
        "description": product.localized("description"),
        "image": facts.image_urls,
        "sku": str(product.pk),
        "brand": {"@type": "Brand", "name": settings.BRAND_NAME},
        "material": product.localized("shell_material"),
        "offers": offers_json_ld(facts),
    }


def offers_json_ld(facts: ProductFacts) -> dict:
    prices = facts.prices
    availability = f"{SCHEMA}/{'OutOfStock' if prices.sold_out else 'InStock'}"
    common = {"priceCurrency": "RUB", "availability": availability, "url": facts.canonical_url}
    if prices.is_from:
        return {
            "@type": "AggregateOffer",
            "lowPrice": whole_rubles(prices.low_kopecks),
            "highPrice": whole_rubles(prices.high_kopecks),
            **common,
        }
    return {"@type": "Offer", "price": whole_rubles(prices.low_kopecks), **common}


def whole_rubles(kopecks: int | None) -> str:
    return str(round((kopecks or 0) / 100))


def breadcrumb_json_ld(crumbs: list[tuple[str, str]]) -> dict:
    """`crumbs`: (name, absolute URL) pairs from the catalog home to the current page."""
    return {
        "@context": SCHEMA,
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": position, "name": name, "item": url}
            for position, (name, url) in enumerate(crumbs, start=1)
        ],
    }


def as_script(data: dict) -> SafeString:
    """Serialises JSON-LD for a `<script>` element, escaping characters that could close it."""
    text = json.dumps(data, ensure_ascii=False)
    escaped = text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return mark_safe(f'<script type="application/ld+json">{escaped}</script>')
