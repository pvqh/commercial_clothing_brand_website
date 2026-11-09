from decimal import Decimal

from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django_stubs_ext import StrOrPromise

from .choices import Size
from .timestamped import TimestampedModel
from .translated import TranslatedModel

MEASUREMENT_FIELDS = ("chest_cm", "waist_cm", "hips_cm", "sleeve_cm", "length_cm")


def measurement_field(label: StrOrPromise) -> models.DecimalField:
    return models.DecimalField(label, max_digits=5, decimal_places=1)


class SizeGuide(TranslatedModel, TimestampedModel):
    internal_name = models.CharField(_("internal name"), max_length=100)
    how_to_measure_ru = models.TextField(_("how to measure (Russian)"))
    how_to_measure_en = models.TextField(_("how to measure (English)"), blank=True)

    class Meta:
        ordering = ["internal_name"]
        verbose_name = _("size guide")
        verbose_name_plural = _("size guides")

    def __str__(self) -> str:
        return self.internal_name


class SizeGuideRow(TimestampedModel):
    size_guide = models.ForeignKey(SizeGuide, on_delete=models.CASCADE, related_name="rows")
    size = models.PositiveSmallIntegerField(
        _("size"), choices=[(size.value, size.label) for size in Size.letter_sizes()]
    )
    chest_cm = measurement_field(_("chest, cm"))
    waist_cm = measurement_field(_("waist, cm"))
    hips_cm = measurement_field(_("hips, cm"))
    sleeve_cm = measurement_field(_("sleeve, cm"))
    length_cm = measurement_field(_("length, cm"))

    class Meta:
        ordering = ["size_guide", "size"]
        verbose_name = _("size guide row")
        verbose_name_plural = _("size guide rows")
        constraints = [
            models.UniqueConstraint(fields=["size_guide", "size"], name="sizeguiderow_unique_size"),
            models.CheckConstraint(
                condition=Q(size__lt=Size.ONE), name="sizeguiderow_not_one_size"
            ),
            *[
                models.CheckConstraint(
                    condition=Q(**{f"{name}__gt": Decimal(0)}), name=f"sizeguiderow_{name}_positive"
                )
                for name in MEASUREMENT_FIELDS
            ],
        ]

    def __str__(self) -> str:
        return f"{self.size_guide} / {Size(self.size).label}"


class ProductType(TranslatedModel, TimestampedModel):
    """Groups products that share a size guide (FR-028). Shown to staff only."""

    name_ru = models.CharField(_("name (Russian)"), max_length=80)
    name_en = models.CharField(_("name (English)"), max_length=80, blank=True)
    size_guide = models.ForeignKey(
        SizeGuide,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="product_types",
        verbose_name=_("default size guide"),
    )

    class Meta:
        ordering = ["name_ru"]
        verbose_name = _("product type")
        verbose_name_plural = _("product types")

    def __str__(self) -> str:
        return self.name_ru
