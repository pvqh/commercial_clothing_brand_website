from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _
from django_stubs_ext import StrOrPromise

from catalog.services.slugs import assign_slugs

from .category import Category
from .choices import FurTreatment, Size
from .size_guide import ProductType, SizeGuide
from .timestamped import TimestampedModel
from .translated import TranslatedModel

REQUIRED_TRANSLATED_FIELDS = (
    "name",
    "description",
    "care_instructions",
    "fur_species",
    "fur_origin_country",
    "shell_material",
    "lining_material",
)


def text_pair(
    label: StrOrPromise, max_length: int | None = None, required: bool = True
) -> tuple[models.Field, models.Field]:
    """The Russian and English columns of one translated field (research R6)."""
    return (
        text_column(format_lazy("{} (RU)", label), max_length, blank=not required),
        text_column(format_lazy("{} (EN)", label), max_length, blank=True),
    )


def text_column(label: StrOrPromise, max_length: int | None, blank: bool) -> models.Field:
    if max_length:
        return models.CharField(label, max_length=max_length, blank=blank)
    return models.TextField(label, blank=blank)


class Product(TranslatedModel, TimestampedModel):
    name_ru, name_en = text_pair(_("name"), 150)
    description_ru, description_en = text_pair(_("description"))
    care_instructions_ru, care_instructions_en = text_pair(_("care"))
    fur_species_ru, fur_species_en = text_pair(_("fur species"), 100)
    fur_origin_country_ru, fur_origin_country_en = text_pair(_("fur origin country"), 100)
    fur_treatment = models.CharField(_("fur treatment"), max_length=10, choices=FurTreatment)
    fur_treatment_detail_ru, fur_treatment_detail_en = text_pair(
        _("treatment detail"), 200, required=False
    )
    shell_material_ru, shell_material_en = text_pair(_("shell"), 200)
    lining_material_ru, lining_material_en = text_pair(_("lining"), 200)
    trim_material_ru, trim_material_en = text_pair(_("trim"), 200, required=False)
    product_type = models.ForeignKey(
        ProductType,
        on_delete=models.PROTECT,
        null=True,
        related_name="products",
        verbose_name=_("product type"),
    )
    size_guide = models.ForeignKey(
        SizeGuide,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="products",
        verbose_name=_("size guide override"),
    )
    categories = models.ManyToManyField(
        Category, through="ProductCategory", related_name="products"
    )
    slug_ru = models.SlugField(max_length=160, unique=True, editable=False)
    slug_en = models.SlugField(max_length=160, unique=True, editable=False)
    is_published = models.BooleanField(_("published"), default=False, editable=False)
    first_published_at = models.DateTimeField(_("first published"), null=True, editable=False)

    class Meta:
        verbose_name = _("product")
        verbose_name_plural = _("products")
        indexes = [models.Index(fields=["is_published", "first_published_at"])]

    def __str__(self) -> str:
        return self.name_ru

    def save(self, *args, **kwargs) -> None:
        with transaction.atomic():
            assign_slugs(self)
            super().save(*args, **kwargs)

    def clean(self) -> None:
        if self.fur_treatment == FurTreatment.TREATED and not self.fur_treatment_detail_ru.strip():
            raise ValidationError(
                {"fur_treatment_detail_ru": _("Describe the treatment when the fur is treated.")}
            )

    @property
    def variants(self) -> models.QuerySet:
        from .color_variant import Variant

        return Variant.objects.filter(color__product=self)

    @property
    def primary_category(self) -> Category | None:
        membership = (
            self.category_memberships.select_related("category").order_by("position").first()
        )
        return membership.category if membership else None

    @property
    def effective_size_guide(self) -> SizeGuide | None:
        if self.size_guide_id:
            return self.size_guide
        return self.product_type.size_guide if self.product_type else None

    @property
    def is_one_size(self) -> bool:
        sizes = set(self.variants.values_list("size", flat=True))
        return sizes == {Size.ONE}

    @property
    def is_sold_out(self) -> bool:
        return not self.variants.filter(stock__gt=0).exists()

    @property
    def missing_english(self) -> bool:
        if any(not getattr(self, f"{name}_en").strip() for name in REQUIRED_TRANSLATED_FIELDS):
            return True
        return (
            self.colors.filter(name_en="").exists() or self.photos.filter(alt_text_en="").exists()
        )

    def missing_russian_fields(self) -> list[str]:
        missing = [
            name for name in REQUIRED_TRANSLATED_FIELDS if not getattr(self, f"{name}_ru").strip()
        ]
        if self.fur_treatment == FurTreatment.TREATED and not self.fur_treatment_detail_ru.strip():
            missing.append("fur_treatment_detail")
        return missing


class ProductCategory(TimestampedModel):
    """A product's membership of a category; position 0 is the primary category (FR-002)."""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="category_memberships"
    )
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="product_memberships"
    )
    position = models.PositiveSmallIntegerField(_("position"), default=0)

    class Meta:
        ordering = ["product", "position"]
        verbose_name = _("category membership")
        verbose_name_plural = _("category memberships")
        constraints = [
            models.UniqueConstraint(
                fields=["product", "category"], name="productcategory_unique_category"
            ),
            models.UniqueConstraint(
                fields=["product", "position"], name="productcategory_unique_position"
            ),
        ]
        indexes = [models.Index(fields=["category", "product"])]

    def __str__(self) -> str:
        return f"{self.product} → {self.category}"
