from django import forms
from django.contrib import admin, messages
from django.db.models import Exists, OuterRef, Q
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from audit.admin import AuditedModelAdmin, change_set_of, stored_copy
from audit.recording import record_update
from catalog.models import Color, Product, ProductCategory, ProductPhoto, Variant
from catalog.models.product import REQUIRED_TRANSLATED_FIELDS
from catalog.services.photo_renditions import generate_renditions
from catalog.services.publishing import PublishRuleError, publish

from .labelled_inline import LabelledTabularInline
from .publishing_actions import unpublish_selected


class MissingEnglishFilter(admin.SimpleListFilter):
    """Products with any required text, color name or photo description missing in English."""

    title = gettext_lazy("Missing English")
    parameter_name = "missing_english"

    def lookups(self, request, model_admin):
        return [("yes", _("Yes"))]

    def queryset(self, request, queryset):
        if self.value() != "yes":
            return queryset
        missing = Q(colors__name_en="") | Q(photos__alt_text_en="")
        for name in REQUIRED_TRANSLATED_FIELDS:
            missing |= Q(**{f"{name}_en": ""})
        return queryset.filter(missing).distinct()


class SoldOutFilter(admin.SimpleListFilter):
    title = gettext_lazy("Sold out")
    parameter_name = "sold_out"

    def lookups(self, request, model_admin):
        return [("yes", _("Yes")), ("no", _("No"))]

    def queryset(self, request, queryset):
        in_stock = Exists(Variant.objects.filter(color__product=OuterRef("pk"), stock__gt=0))
        if self.value() == "yes":
            return queryset.filter(~in_stock)
        if self.value() == "no":
            return queryset.filter(in_stock)
        return queryset


class CategoryMembershipInline(LabelledTabularInline):
    model = ProductCategory
    fields = ["category", "position"]
    ordering = ["position"]
    extra = 1
    verbose_name_plural = gettext_lazy("Categories (position 0 is the primary category)")


class ColorInline(LabelledTabularInline):
    model = Color
    fields = ["name_ru", "name_en", "position"]
    ordering = ["position"]
    extra = 1
    show_change_link = True
    verbose_name_plural = gettext_lazy("Colors (open a color to edit its sizes, prices and stock)")


class PhotoInline(LabelledTabularInline):
    model = ProductPhoto
    fields = ["original", "color", "position", "alt_text_ru", "alt_text_en"]
    ordering = ["position", "id"]
    extra = 1

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "color":
            product_id = request.resolver_match.kwargs.get("object_id")
            kwargs["queryset"] = Color.objects.filter(product_id=product_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.action(description=gettext_lazy("Publish selected"))
def publish_selected(modeladmin, request, queryset) -> None:
    published = 0
    for product in queryset:
        before = stored_copy(product)
        try:
            publish(product)
        except PublishRuleError as refusal:
            report_refusal(request, refusal)
            continue
        record_update(before, product, request.user, change_set_of(request))
        published += 1
    if published:
        messages.success(request, _("Published: %(count)s.") % {"count": published})


def report_refusal(request, refusal: PublishRuleError) -> None:
    message = _("«%(product)s» was not published: %(rules)s")
    rules = " ".join(refusal.failures)
    messages.error(request, message % {"product": refusal.product, "rules": rules})


@admin.register(Product)
class ProductAdmin(AuditedModelAdmin):
    list_display = ["name_ru", "primary_category_name", "is_published", "english", "in_stock"]
    list_filter = [
        "is_published",
        "category_memberships__category",
        "product_type",
        MissingEnglishFilter,
        SoldOutFilter,
    ]
    search_fields = ["name_ru", "name_en"]
    actions = [publish_selected, unpublish_selected]
    readonly_fields = ["is_published", "first_published_at", "slug_ru", "slug_en"]
    inlines = [CategoryMembershipInline, ColorInline, PhotoInline]
    fieldsets = [
        (
            gettext_lazy("Texts"),
            {
                "fields": [
                    ("name_ru", "name_en"),
                    ("description_ru", "description_en"),
                    ("care_instructions_ru", "care_instructions_en"),
                ]
            },
        ),
        (
            gettext_lazy("Fur and materials"),
            {
                "fields": [
                    "fur_treatment",
                    ("fur_species_ru", "fur_species_en"),
                    ("fur_origin_country_ru", "fur_origin_country_en"),
                    ("fur_treatment_detail_ru", "fur_treatment_detail_en"),
                    ("shell_material_ru", "shell_material_en"),
                    ("lining_material_ru", "lining_material_en"),
                    ("trim_material_ru", "trim_material_en"),
                ]
            },
        ),
        (gettext_lazy("Type and size guide"), {"fields": ["product_type", "size_guide"]}),
        (
            gettext_lazy("Publication"),
            {"fields": ["is_published", "first_published_at", "slug_ru", "slug_en"]},
        ),
    ]

    def has_delete_permission(self, request, obj=None) -> bool:
        """Products are unpublished, never deleted (research R8)."""
        return False

    def after_row_saved(self, obj, before) -> None:
        if isinstance(obj, ProductPhoto) and photo_file_changed(obj, before):
            generate_renditions(obj)

    @admin.display(description=gettext_lazy("primary category"))
    def primary_category_name(self, product: Product) -> str:
        category = product.primary_category
        return category.name_ru if category else "—"

    @admin.display(description=gettext_lazy("English filled in"), boolean=True)
    def english(self, product: Product) -> bool:
        return not product.missing_english

    @admin.display(description=gettext_lazy("in stock"), boolean=True)
    def in_stock(self, product: Product) -> bool:
        return not product.is_sold_out


def photo_file_changed(photo: ProductPhoto, before: ProductPhoto | None) -> bool:
    return before is None or before.original.name != photo.original.name


class VariantForm(forms.ModelForm):
    """Staff enter prices in whole rubles; they are stored in kopecks (research R15)."""

    price_rub = forms.IntegerField(label=gettext_lazy("price, ₽"), min_value=1)
    stock = forms.IntegerField(label=gettext_lazy("stock"), min_value=0)

    class Meta:
        model = Variant
        fields = ["size", "price_rub", "stock"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial["price_rub"] = self.instance.price_kopecks // 100

    def save(self, commit: bool = True) -> Variant:
        self.instance.price_kopecks = self.cleaned_data["price_rub"] * 100
        return super().save(commit)


class VariantInline(LabelledTabularInline):
    model = Variant
    form = VariantForm
    ordering = ["size"]
    extra = 1


@admin.register(Color)
class ColorAdmin(AuditedModelAdmin):
    list_display = ["product", "name_ru", "name_en", "position"]
    search_fields = ["product__name_ru", "name_ru"]
    fields = ["product", ("name_ru", "name_en"), "position"]
    inlines = [VariantInline]

    def get_readonly_fields(self, request, obj=None):
        return ["product"] if obj else []
