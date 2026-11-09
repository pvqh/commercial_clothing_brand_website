"""Staff accounts, managed by the admin only: create, rename, disable. Never deleted (FR-044)."""

from django.contrib import admin
from django.contrib.admin.utils import unquote
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.utils.translation import gettext_lazy

from audit.admin import AuditedModelAdmin, change_set_of
from audit.recording import record_update
from catalog.staff_group import ensure_staff_group

User = get_user_model()


class StaffCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name")


admin.site.unregister(User)


@admin.register(User)
class StaffAccountAdmin(AuditedModelAdmin, UserAdmin):
    add_form = StaffCreationForm
    list_display = ["username", "first_name", "last_name", "is_active", "is_superuser"]
    list_filter = ["is_active", "is_superuser"]
    actions = None
    fieldsets = [
        (None, {"fields": ["username", "password"]}),
        (gettext_lazy("Name"), {"fields": ["first_name", "last_name"]}),
        (gettext_lazy("Access"), {"fields": ["is_active"]}),
    ]
    add_fieldsets = [
        (
            None,
            {"fields": ["username", "first_name", "last_name", "password1", "password2"]},
        ),
    ]

    def has_module_permission(self, request) -> bool:
        return request.user.is_active and request.user.is_superuser

    def has_view_permission(self, request, obj=None) -> bool:
        return self.has_module_permission(request)

    def has_add_permission(self, request) -> bool:
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None) -> bool:
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def save_model(self, request, obj, form, change) -> None:
        if not change:
            obj.is_staff = True
        super().save_model(request, obj, form, change)
        if not change:
            obj.groups.add(ensure_staff_group())

    def user_change_password(self, request, id, form_url=""):
        """Records a password reset as a change, storing only the marker "changed"."""
        with transaction.atomic():
            before = User.objects.get(pk=unquote(id))
            response = super().user_change_password(request, id, form_url)
            after = User.objects.get(pk=before.pk)
            record_update(before, after, request.user, change_set_of(request))
        return response
