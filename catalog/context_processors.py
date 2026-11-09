from django.conf import settings
from django.http import HttpRequest

from catalog.models import Category


def navigation(request: HttpRequest) -> dict:
    """Categories shown in the header and footer: published and with a published product."""
    categories = (
        Category.objects.filter(is_published=True, product_memberships__product__is_published=True)
        .distinct()
        .order_by("position", "id")
    )
    return {"navigation_categories": categories, "brand_name": settings.BRAND_NAME}
