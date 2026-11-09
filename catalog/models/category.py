from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from catalog.services.slugs import assign_slugs

from .timestamped import TimestampedModel
from .translated import TranslatedModel


class Category(TranslatedModel, TimestampedModel):
    """A flat group of products that shoppers browse (FR-001)."""

    name_ru = models.CharField(_("name (Russian)"), max_length=80)
    name_en = models.CharField(_("name (English)"), max_length=80, blank=True)
    slug_ru = models.SlugField(max_length=100, unique=True, editable=False)
    slug_en = models.SlugField(max_length=100, unique=True, editable=False)
    position = models.PositiveSmallIntegerField(_("position"), default=0)
    is_published = models.BooleanField(_("published"), default=False)

    class Meta:
        ordering = ["position", "id"]
        verbose_name = _("category")
        verbose_name_plural = _("categories")

    def __str__(self) -> str:
        return self.name_ru

    def save(self, *args, **kwargs) -> None:
        with transaction.atomic():
            assign_slugs(self)
            super().save(*args, **kwargs)
