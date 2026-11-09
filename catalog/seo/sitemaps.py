"""`/sitemap.xml`: published categories and products in both languages (R11, Principle IV)."""

from django.contrib.sitemaps import Sitemap
from django.db.models import QuerySet

from catalog.models import Category, Product
from catalog.views.addresses import active_language, category_path, product_path


class BilingualSitemap(Sitemap):
    i18n = True
    languages = ["ru", "en"]
    alternates = True
    x_default = True


class CategorySitemap(BilingualSitemap):
    def items(self) -> QuerySet[Category]:
        return (
            Category.objects.filter(
                is_published=True, product_memberships__product__is_published=True
            )
            .distinct()
            .order_by("position", "id")
        )

    def location(self, item: Category) -> str:
        return category_path(item, active_language())

    def lastmod(self, item: Category):
        return item.updated_at


class ProductSitemap(BilingualSitemap):
    def items(self) -> QuerySet[Product]:
        return Product.objects.filter(is_published=True).order_by("id")

    def location(self, item: Product) -> str:
        return product_path(item, active_language())

    def lastmod(self, item: Product):
        return item.updated_at


SITEMAPS = {"categories": CategorySitemap, "products": ProductSitemap}
