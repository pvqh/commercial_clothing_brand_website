from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.translation import gettext as _

from catalog.models import Category
from catalog.services.listing_query import published_listing

from .addresses import LANGUAGES, absolute, active_language, home_path
from .caching import public_cache

PRODUCTS_PER_SECTION = 4


@public_cache
def home_page(request: HttpRequest) -> HttpResponse:
    language = active_language()
    categories = Category.objects.filter(
        is_published=True, product_memberships__product__is_published=True
    ).distinct()
    sections = [
        {"category": category, "products": published_listing(category)[:PRODUCTS_PER_SECTION]}
        for category in categories.order_by("position", "id")
    ]
    context = {
        "sections": sections,
        "page_title": _("Catalog"),
        "meta_description": _("Fur coats and accessories: the full catalog with prices and sizes."),
        "canonical_url": absolute(request, home_path(language)),
        "alternate_urls": {lang: home_path(lang) for lang in LANGUAGES},
    }
    return render(request, "catalog/home.html", context)
