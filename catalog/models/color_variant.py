from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from .choices import Size
from .product import Product
from .timestamped import TimestampedModel
from .translated import TranslatedModel


class Color(TranslatedModel, TimestampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="colors")
    name_ru = models.CharField(_("name (Russian)"), max_length=60)
    name_en = models.CharField(_("name (English)"), max_length=60, blank=True)
    position = models.PositiveSmallIntegerField(_("position"), default=0)

    class Meta:
        ordering = ["product", "position"]
        verbose_name = _("color")
        verbose_name_plural = _("colors")
        constraints = [
            models.UniqueConstraint(fields=["product", "position"], name="color_unique_position"),
        ]

    def __str__(self) -> str:
        return f"{self.product}, {self.name_ru}"

    @property
    def is_out_of_stock(self) -> bool:
        return not self.variants.filter(stock__gt=0).exists()


class Variant(TimestampedModel):
    """One buyable size in one color (FR-019)."""

    color = models.ForeignKey(Color, on_delete=models.CASCADE, related_name="variants")
    size = models.PositiveSmallIntegerField(_("size"), choices=Size)
    price_kopecks = models.PositiveBigIntegerField(_("price, kopecks"))
    stock = models.IntegerField(_("stock"), default=0)

    class Meta:
        ordering = ["color", "size"]
        verbose_name = _("variant")
        verbose_name_plural = _("variants")
        constraints = [
            models.UniqueConstraint(fields=["color", "size"], name="variant_unique_size"),
            models.CheckConstraint(condition=Q(price_kopecks__gt=0), name="variant_price_positive"),
            models.CheckConstraint(condition=Q(stock__gte=0), name="variant_stock_not_negative"),
        ]
        indexes = [
            models.Index(
                fields=["color", "size"], condition=Q(stock__gt=0), name="variant_in_stock_idx"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.color} / {Size(self.size).label}"

    def clean(self) -> None:
        if self.color_id and self.mixes_one_size_with_letter_sizes():
            raise ValidationError({"size": _("A product cannot mix “One size” with letter sizes.")})

    def mixes_one_size_with_letter_sizes(self) -> bool:
        other_sizes = Variant.objects.filter(color__product_id=self.color.product_id).exclude(
            pk=self.pk
        )
        if self.size == Size.ONE:
            return other_sizes.exclude(size=Size.ONE).exists()
        return other_sizes.filter(size=Size.ONE).exists()
