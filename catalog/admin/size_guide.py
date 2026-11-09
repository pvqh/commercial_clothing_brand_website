from django.contrib import admin

from audit.admin import AuditedModelAdmin
from catalog.models import ProductType, SizeGuide, SizeGuideRow

from .labelled_inline import LabelledTabularInline


@admin.register(ProductType)
class ProductTypeAdmin(AuditedModelAdmin):
    list_display = ["name_ru", "name_en", "size_guide"]
    fields = [("name_ru", "name_en"), "size_guide"]


class SizeGuideRowInline(LabelledTabularInline):
    model = SizeGuideRow
    fields = ["size", "chest_cm", "waist_cm", "hips_cm", "sleeve_cm", "length_cm"]
    ordering = ["size"]
    extra = 1


@admin.register(SizeGuide)
class SizeGuideAdmin(AuditedModelAdmin):
    list_display = ["internal_name"]
    fields = ["internal_name", ("how_to_measure_ru", "how_to_measure_en")]
    inlines = [SizeGuideRowInline]
