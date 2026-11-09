"""Publish / unpublish actions that go through the change history one object at a time (R9)."""

from collections.abc import Callable
from typing import Any

from django.contrib import admin, messages
from django.db import models
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from audit.admin import change_set_of, stored_copy
from audit.recording import record_update


def set_published(request, obj: models.Model, change: Callable) -> None:
    before = stored_copy(obj)
    change(obj)
    record_update(before, obj, request.user, change_set_of(request))


def mark_published(obj: Any) -> None:
    obj.is_published = True
    obj.save()


def mark_unpublished(obj: Any) -> None:
    obj.is_published = False
    obj.save()


@admin.action(description=gettext_lazy("Unpublish selected"))
def unpublish_selected(modeladmin, request, queryset) -> None:
    for obj in queryset:
        set_published(request, obj, mark_unpublished)
    messages.success(request, _("Unpublished: %(count)s.") % {"count": queryset.count()})
