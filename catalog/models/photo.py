from django.db import models
from django.utils.translation import gettext_lazy as _

from .color_variant import Color
from .product import Product
from .timestamped import TimestampedModel
from .translated import TranslatedModel

RENDITION_WIDTHS = (360, 720, 1080, 1440)


class ProductPhoto(TranslatedModel, TimestampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="photos")
    color = models.ForeignKey(
        Color,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="photos",
        verbose_name=_("color"),
        help_text=_("Leave empty for a photo shared by every color."),
    )
    position = models.PositiveSmallIntegerField(_("position"), default=0)
    original = models.ImageField(
        _("photo"), upload_to="photos/originals/", width_field="width", height_field="height"
    )
    width = models.PositiveIntegerField(editable=False)
    height = models.PositiveIntegerField(editable=False)
    alt_text_ru = models.CharField(_("alt text (Russian)"), max_length=250)
    alt_text_en = models.CharField(_("alt text (English)"), max_length=250, blank=True)

    class Meta:
        ordering = ["product", "position", "id"]
        verbose_name = _("photo")
        verbose_name_plural = _("photos")

    def __str__(self) -> str:
        return self.alt_text_ru or f"{self.product} #{self.position}"

    def save(self, *args, **kwargs) -> None:
        if self.original and not (self.width and self.height):
            self.width, self.height = self.original.width, self.original.height
        super().save(*args, **kwargs)

    @property
    def cropped_width(self) -> int:
        """The width left after cropping the original to the 2:3 photo standard."""
        return min(self.width, round(self.height * 2 / 3))

    def rendition_widths(self) -> list[int]:
        return [width for width in RENDITION_WIDTHS if width <= self.cropped_width]
