from django.core.paginator import Page, Paginator
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import gettext as _

from catalog.models import Category, CategorySlugRedirect
from catalog.services.listing_filters import ListingFilters, Sort
from catalog.services.listing_query import filtered_listing, offered_sizes

from .addresses import LANGUAGES, absolute, active_language, category_path, home_path
from .caching import public_cache
from .pagination import PRODUCTS_PER_PAGE, normalised_page, page_navigation
from .slug_lookup import published_by_slug, redirect_from_old_slug


@public_cache
def category_page(request: HttpRequest, slug: str) -> HttpResponse:
    category = published_by_slug(Category, slug)
    if category is None:
        return redirect_from_old_slug(request, CategorySlugRedirect, slug, category_path)
    filters = ListingFilters.from_query(request.GET)
    paginator = Paginator(filtered_listing(category, filters), PRODUCTS_PER_PAGE)
    page_number = normalised_page(request.GET.get("page"), paginator.num_pages)
    query = filters.query_string(page_number)
    if request.META.get("QUERY_STRING", "") != query.removeprefix("?"):
        return HttpResponseRedirect(category_path(category, active_language(), query))
    page = paginator.page(page_number or 1)
    context = listing_context(request, category, page) | filter_context(category, filters, page)
    response = render(request, "catalog/category.html", context)
    if request.headers.get("HX-Request"):
        response["HX-Push-Url"] = request.get_full_path()
    return response


def listing_context(request: HttpRequest, category: Category, page: Page) -> dict:
    language = active_language()
    unfiltered_query = ListingFilters().query_string(page.number)
    name = category.localized("name")
    return {
        "category": category,
        "current_category": category,
        "page_obj": page,
        "page_title": listing_title(name, page.number),
        "meta_description": _("%(category)s: %(count)s products in the catalog.")
        % {"category": name, "count": page.paginator.count},
        "canonical_url": absolute(request, category_path(category, language, unfiltered_query)),
        "alternate_urls": {
            lang: category_path(category, lang, unfiltered_query) for lang in LANGUAGES
        },
        "crumbs": [{"label": _("Catalog"), "url": home_path(language)}, {"label": name}],
    }


def filter_context(category: Category, filters: ListingFilters, page: Page) -> dict:
    """Filter form state, remove links and paging that keep the chosen filters (FR-010)."""
    language = active_language()

    def address(view_filters: ListingFilters, page_number: int | None = None) -> str:
        return category_path(category, language, view_filters.query_string(page_number))

    return {
        "filters": filters,
        "sort_choices": Sort.choices,
        "offered_sizes": offered_sizes(category),
        "chosen_size_codes": [size.code for size in filters.sizes],
        "active_filters": active_filter_links(filters, address),
        "unfiltered_url": address(ListingFilters()),
        "pages": page_navigation(page, lambda number: address(filters, number)),
        "noindex": page.paginator.count == 0 or not filters.is_default,
    }


def active_filter_links(filters: ListingFilters, address) -> list[dict]:
    links = [
        {"label": size.label, "url": address(filters.without_size(size))} for size in filters.sizes
    ]
    if filters.has_price:
        links.append({"label": price_label(filters), "url": address(filters.without_price())})
    return links


def price_label(filters: ListingFilters) -> str:
    if filters.price_min is not None and filters.price_max is not None:
        return _("%(low)s–%(high)s ₽") % {"low": filters.price_min, "high": filters.price_max}
    if filters.price_min is not None:
        return _("from %(low)s ₽") % {"low": filters.price_min}
    return _("up to %(high)s ₽") % {"high": filters.price_max}


def listing_title(category_name: str, page_number: int) -> str:
    if page_number == 1:
        return category_name
    return _("%(category)s — page %(page)s") % {"category": category_name, "page": page_number}
