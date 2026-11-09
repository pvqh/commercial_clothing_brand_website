from django.db import models

from .category import Category
from .product import Product


class SlugRedirect(models.Model):
    """A slug an entity used to have; requests to it answer 301 to the current slug (FR-025)."""

    language = models.CharField(max_length=2, choices=[("ru", "ru"), ("en", "en")])
    old_slug = models.SlugField(max_length=160)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return f"{self.language}: {self.old_slug}"


class CategorySlugRedirect(SlugRedirect):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="slug_redirects")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["language", "old_slug"], name="categoryslugredirect_unique"
            ),
        ]

    @property
    def owner(self) -> Category:
        return self.category


class ProductSlugRedirect(SlugRedirect):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="slug_redirects")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["language", "old_slug"], name="productslugredirect_unique"
            ),
        ]

    @property
    def owner(self) -> Product:
        return self.product
