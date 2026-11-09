from django.contrib import admin, messages
from django.db.models import Count
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from audit.admin import AuditedModelAdmin
from catalog.models import Category

from .publishing_actions import mark_published, set_published, unpublish_selected


@admin.action(description=gettext_lazy("Publish selected"))
def publish_categories(modeladmin, request, queryset) -> None:
    for category in queryset:
        set_published(request, category, mark_published)
    messages.success(request, _("Published: %(count)s.") % {"count": queryset.count()})


@admin.register(Category)
class CategoryAdmin(AuditedModelAdmin):
    list_display = ["name_ru", "name_en", "position", "is_published", "product_count"]
    list_editable = ["position"]
    ordering = ["position", "id"]
    fields = [("name_ru", "name_en"), "position", "is_published", "slug_ru", "slug_en"]
    readonly_fields = ["slug_ru", "slug_en"]
    actions = [publish_categories, unpublish_selected]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(products_total=Count("product_memberships"))

    @admin.display(description=gettext_lazy("products"), ordering="products_total")
    def product_count(self, category: Category) -> int:
        return category.products_total  # type: ignore[attr-defined]

    def has_delete_permission(self, request, obj=None) -> bool:
        """Categories are unpublished, never deleted (research R8)."""
        return False
