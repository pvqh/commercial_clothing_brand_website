from django.core.files.storage import default_storage
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.text import Truncator
from django.utils.translation import gettext as _

from catalog.models import Color, Product, ProductPhoto, ProductSlugRedirect
from catalog.seo.structured_data import (
    ProductFacts,
    as_script,
    breadcrumb_json_ld,
    product_json_ld,
)
from catalog.services.photo_renditions import rendition_path
from catalog.services.product_availability import (
    availability_for,
    color_states,
    price_range,
)
from catalog.services.size_guides import size_guide_table

from .addresses import LANGUAGES, absolute, active_language, category_path, home_path, product_path
from .caching import public_cache
from .slug_lookup import published_by_slug, redirect_from_old_slug

OPEN_GRAPH_WIDTH = 1080


@public_cache
def product_page(request: HttpRequest, slug: str) -> HttpResponse:
    product = published_by_slug(Product, slug)
    if product is None:
        return redirect_from_old_slug(request, ProductSlugRedirect, slug, product_path)
    try:
        color = chosen_color(product, request.GET.get("color"))
    except Color.DoesNotExist:
        return HttpResponseRedirect(product_path(product, active_language()))
    context = seo_context(request, product) | options_context(product, color)
    context["noindex"] = "color" in request.GET
    return render(request, "catalog/product.html", context)


def chosen_color(product: Product, raw_color_id: str | None) -> Color | None:
    """The color from `?color=`, or the default (position 0); raises if it is not this product's."""
    if raw_color_id is None:
        return product.colors.order_by("position").first()
    if not raw_color_id.isdigit():
        raise Color.DoesNotExist
    return product.colors.get(pk=int(raw_color_id))


def options_context(product: Product, color: Color | None) -> dict:
    """Gallery, colors, sizes and price for the chosen color (FR-019–FR-023)."""
    colors = color_states(product)
    sizes = availability_for(product, color) if color else []
    return {
        "product": product,
        "primary_category": product.primary_category,
        "gallery": color_gallery(product, color),
        "selected_color": color,
        "color_options": colors if len(colors) > 1 else [],
        "size_options": [] if product.is_one_size else sizes,
        "size_guide": None if product.is_one_size else size_guide_table(product),
        "prices": price_range(product, color) if sizes else price_range(product),
        "is_sold_out": product.is_sold_out,
    }


def seo_context(request: HttpRequest, product: Product) -> dict:
    language = active_language()
    canonical_url = absolute(request, product_path(product, language))
    crumbs = product_crumbs(product, language)
    image_urls = photo_urls(request, shared_gallery(product))
    facts = ProductFacts(product, canonical_url, image_urls, price_range(product))
    return {
        "crumbs": crumbs,
        "page_title": product.localized("name"),
        "meta_description": Truncator(product.localized("description")).chars(160),
        "canonical_url": canonical_url,
        "alternate_urls": {lang: product_path(product, lang) for lang in LANGUAGES},
        "og_image": image_urls[0] if image_urls else "",
        "product_json_ld": as_script(product_json_ld(facts)),
        "breadcrumb_json_ld": as_script(breadcrumb_json_ld(absolute_crumbs(request, crumbs))),
    }


def color_gallery(product: Product, color: Color | None) -> list[ProductPhoto]:
    """The color's own photos, or the shared photos when it has none (edge case)."""
    if color is not None:
        own_photos = list(color.photos.order_by("position", "id"))
        if own_photos:
            return own_photos
    return shared_gallery(product)


def shared_gallery(product: Product) -> list[ProductPhoto]:
    """Photos shared by every color, or all photos when the product has no shared ones."""
    photos = list(product.photos.order_by("position", "id"))
    shared = [photo for photo in photos if photo.color_id is None]
    return shared or photos


def product_crumbs(product: Product, language: str) -> list[dict]:
    crumbs = [{"label": _("Catalog"), "url": home_path(language)}]
    category = product.primary_category
    if category is not None:
        crumbs.append(
            {"label": category.localized("name"), "url": category_path(category, language)}
        )
    crumbs.append({"label": product.localized("name"), "url": product_path(product, language)})
    return crumbs


def absolute_crumbs(request: HttpRequest, crumbs: list[dict]) -> list[tuple[str, str]]:
    return [(crumb["label"], absolute(request, crumb["url"])) for crumb in crumbs]


def photo_urls(request: HttpRequest, photos: list[ProductPhoto]) -> list[str]:
    return [absolute(request, open_graph_image_path(photo)) for photo in photos]


def open_graph_image_path(photo: ProductPhoto) -> str:
    widths = [width for width in photo.rendition_widths() if width <= OPEN_GRAPH_WIDTH]
    if not widths:
        return photo.original.url
    return default_storage.url(rendition_path(photo, widths[-1], "jpg"))
