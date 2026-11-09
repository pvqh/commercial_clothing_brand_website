from django.db import models
from django.utils.translation import get_language


def localized_value(instance: object, field_name: str) -> str:
    """The English value on English pages when it is filled in, else the Russian one (FR-036)."""
    russian = getattr(instance, f"{field_name}_ru")
    if (get_language() or "ru").startswith("en"):
        english = getattr(instance, f"{field_name}_en", "")
        if english and english.strip():
            return english
    return russian


class TranslatedModel(models.Model):
    """Base for models whose translated fields are stored as `<field>_ru` / `<field>_en` columns."""

    class Meta:
        abstract = True

    def localized(self, field_name: str) -> str:
        return localized_value(self, field_name)
