"""The size guide on a product page: measurements in centimetres and inches (FR-026–FR-028)."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from django.utils.translation import gettext_lazy as _

from catalog.models import Product, Size
from catalog.models.size_guide import MEASUREMENT_FIELDS

CM_PER_INCH = Decimal("2.54")
MEASUREMENT_LABELS = {
    "chest_cm": _("Chest"),
    "waist_cm": _("Waist"),
    "hips_cm": _("Hips"),
    "sleeve_cm": _("Sleeve"),
    "length_cm": _("Length"),
}


@dataclass(frozen=True)
class Measurement:
    cm: Decimal
    inches: Decimal


@dataclass(frozen=True)
class GuideRow:
    size: Size
    measurements: list[Measurement]

    @property
    def label(self) -> str:
        return str(self.size.label)


@dataclass(frozen=True)
class SizeGuideTable:
    headings: list[str]
    rows: list[GuideRow]
    how_to_measure: str


def inches(cm: Decimal) -> Decimal:
    """Computed when shown, never stored (data-model.md, SizeGuideRow)."""
    return (cm / CM_PER_INCH).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def size_guide_table(product: Product) -> SizeGuideTable | None:
    guide = product.effective_size_guide
    if guide is None:
        return None
    rows = [
        GuideRow(
            size=Size(row.size),
            measurements=[measurement(getattr(row, name)) for name in MEASUREMENT_FIELDS],
        )
        for row in guide.rows.order_by("size")
    ]
    headings = [str(MEASUREMENT_LABELS[name]) for name in MEASUREMENT_FIELDS]
    return SizeGuideTable(headings, rows, guide.localized("how_to_measure"))


def measurement(cm: Decimal) -> Measurement:
    return Measurement(cm=cm, inches=inches(cm))
