"""Addresses of catalog pages in a given language (research R6, R7)."""

from urllib.parse import urlencode

from django.http import HttpRequest
from django.urls import reverse
from django.utils import translation

from catalog.models import Category, Product

LANGUAGES = ("ru", "en")


def active_language() -> str:
    return "en" if (translation.get_language() or "ru").startswith("en") else "ru"


def category_path(category: Category, language: str, query: str = "") -> str:
    with translation.override(language):
        path = reverse("catalog:category", kwargs={"slug": getattr(category, f"slug_{language}")})
    return path + query


def product_path(product: Product, language: str, query: str = "") -> str:
    with translation.override(language):
        path = reverse("catalog:product", kwargs={"slug": getattr(product, f"slug_{language}")})
    return path + query


def home_path(language: str) -> str:
    with translation.override(language):
        return reverse("catalog:home")


def query_string(params: list[tuple[str, str]]) -> str:
    return f"?{urlencode(params)}" if params else ""


def absolute(request: HttpRequest, path: str) -> str:
    return request.build_absolute_uri(path)
