from django.db import models
from django.utils.translation import gettext_lazy as _


class Size(models.IntegerChoices):
    """Garment sizes. The numeric value is the display order (FR-009)."""

    XXS = 10, "XXS"
    XS = 20, "XS"
    S = 30, "S"
    M = 40, "M"
    L = 50, "L"
    XL = 60, "XL"
    XXL = 70, "XXL"
    XXXL = 80, "XXXL"
    ONE = 100, _("One size")

    @property
    def code(self) -> str:
        """The code used in addresses (`?size=m`) and the import workbook."""
        return self.name.lower()

    @classmethod
    def from_code(cls, code: str) -> "Size":
        try:
            return cls[code.strip().upper()]
        except KeyError as unknown:
            raise ValueError(f"Unknown size code: {code!r}") from unknown

    @classmethod
    def letter_sizes(cls) -> list["Size"]:
        return [size for size in cls if size is not cls.ONE]


class FurTreatment(models.TextChoices):
    NATURAL = "natural", _("Natural (not dyed or treated)")
    DYED = "dyed", _("Dyed")
    TREATED = "treated", _("Treated")
