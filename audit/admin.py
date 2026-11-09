"""Staff-area screens that record every change, and the read-only change history with undo."""

import uuid

from django.apps import apps
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db import models
from django.http import HttpRequest, HttpResponseNotAllowed, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.text import Truncator
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from .models import ChangeRecord
from .recording import new_change_set, record_created, record_deleted, record_update
from .undo import UndoRefused, undo


def change_set_of(request: HttpRequest) -> uuid.UUID:
    """One change set per staff request, so everything saved together is shown together."""
    if not hasattr(request, "audit_change_set"):
        request.audit_change_set = new_change_set()  # type: ignore[attr-defined]
    return request.audit_change_set  # type: ignore[attr-defined]


def stored_copy(instance: models.Model) -> models.Model:
    return type(instance)._default_manager.get(pk=instance.pk)


class AuditedModelAdmin(admin.ModelAdmin):
    """Records creates, field changes and deletes, including inline rows, in the save's transaction.

    The Django admin wraps every save and delete view in a transaction, so if writing a record
    fails, the change itself is rolled back (contracts/staff-area.md).
    """

    def save_model(self, request, obj, form, change) -> None:
        before = stored_copy(obj) if change else None
        super().save_model(request, obj, form, change)
        self.record_saved(request, obj, before)

    def save_formset(self, request, form, formset, change) -> None:
        rows = formset.save(commit=False)
        for row in formset.deleted_objects:
            self.delete_row(request, row)
        for row in rows:
            before = stored_copy(row) if row.pk else None
            row.save()
            self.record_saved(request, row, before)
        formset.save_m2m()

    def record_saved(self, request, obj, before: models.Model | None) -> None:
        if before is None:
            record_created(obj, request.user, change_set_of(request))
        else:
            record_update(before, obj, request.user, change_set_of(request))
        self.after_row_saved(obj, before)

    def after_row_saved(self, obj: models.Model, before: models.Model | None) -> None:
        """Hook for follow-up work on a saved row, such as photo renditions."""

    def delete_model(self, request, obj) -> None:
        self.delete_row(request, obj)

    def delete_queryset(self, request, queryset) -> None:
        for obj in queryset:
            self.delete_row(request, obj)

    def delete_row(self, request, row: models.Model) -> None:
        """Deletes a row (photo files stay on disk so undo can restore it, R9)."""
        record_deleted(row, request.user, change_set_of(request))
        row.delete()


@admin.register(ChangeRecord)
class ChangeRecordAdmin(admin.ModelAdmin):
    list_display = [
        "changed_at",
        "staff_name",
        "item_type",
        "entity_label",
        "action",
        "field_name",
        "change",
        "undo_button",
    ]
    list_filter = ["entity_type", "staff", "changed_at", "action"]
    search_fields = ["entity_label"]
    ordering = ["-changed_at", "change_set", "id"]
    list_select_related = ["staff"]
    actions = None
    change_list_template = "admin/audit/changerecord/change_list.html"

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    @admin.display(description=gettext_lazy("staff member"), ordering="staff")
    def staff_name(self, record: ChangeRecord) -> str:
        if record.staff is None:
            return "—"
        return record.staff.get_full_name() or record.staff.get_username()

    @admin.display(description=gettext_lazy("item type"), ordering="entity_type")
    def item_type(self, record: ChangeRecord) -> str:
        for model in apps.get_models():
            if model._meta.model_name == record.entity_type:
                return str(model._meta.verbose_name)
        return record.entity_type

    @admin.display(description=gettext_lazy("old → new"))
    def change(self, record: ChangeRecord) -> str:
        if record.action != ChangeRecord.Action.UPDATED:
            return ""
        return f"{short(record.old_value)} → {short(record.new_value)}"

    @admin.display(description=gettext_lazy("undo"))
    def undo_button(self, record: ChangeRecord) -> str:
        url = reverse("admin:audit_changerecord_undo", args=[record.pk])
        return format_html(
            '<button type="submit" form="undo-form" formaction="{}" class="button">{}</button>',
            url,
            _("Undo"),
        )

    def get_urls(self):
        undo_url = path(
            "<int:record_id>/undo/",
            self.admin_site.admin_view(self.undo_view),
            name="audit_changerecord_undo",
        )
        return [undo_url, *super().get_urls()]

    def undo_view(self, request: HttpRequest, record_id: int):
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])
        if not self.has_view_permission(request):
            raise PermissionDenied
        record = get_object_or_404(ChangeRecord, pk=record_id)
        try:
            undo(record, request.user)
            messages.success(request, _("Change undone"))
        except UndoRefused as refusal:
            messages.error(request, str(refusal))
        return HttpResponseRedirect(back_to_history(request))


def short(value) -> str:
    return Truncator("" if value is None else str(value)).chars(60)


def back_to_history(request: HttpRequest) -> str:
    referer = request.META.get("HTTP_REFERER", "")
    if url_has_allowed_host_and_scheme(referer, {request.get_host()}, request.is_secure()):
        return referer
    return reverse("admin:audit_changerecord_changelist")
