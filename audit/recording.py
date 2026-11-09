"""Writing change records: one per changed field, or a full snapshot for creates and deletes."""

import datetime
import uuid
from decimal import Decimal
from typing import Any

from django.db import models

from .models import ChangeRecord

PASSWORD_MARKER = "changed"
# Derived or bookkeeping columns: kept in snapshots so a deleted row can be recreated exactly,
# but never listed as changes of their own.
UNTRACKED_FIELDS = {"id", "created_at", "updated_at", "slug_ru", "slug_en", "width", "height"}
UNTRACKED_FIELDS |= {"last_login", "date_joined"}


def new_change_set() -> uuid.UUID:
    return uuid.uuid4()


def snapshot(instance: models.Model) -> dict[str, Any]:
    """Every column of the row as JSON-safe values; password hashes become a marker."""
    return {
        field.attname: json_safe(field, getattr(instance, field.attname))
        for field in instance._meta.concrete_fields
    }


def json_safe(field: models.Field, value: Any) -> Any:
    if field.attname == "password":
        return PASSWORD_MARKER
    if isinstance(value, models.fields.files.FieldFile):
        return value.name or ""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime.datetime | datetime.date):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


def changed_fields(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    return [
        name
        for name, value in after.items()
        if name not in UNTRACKED_FIELDS and before.get(name) != value
    ]


def record_update(
    before: models.Model, after: models.Model, staff, change_set: uuid.UUID
) -> list[ChangeRecord]:
    """One `updated` record per field that differs between the stored row and the saved one."""
    old, new = snapshot(before), snapshot(after)
    names = changed_fields(old, new)
    if password_changed(before, after):
        names.append("password")
    records = [field_change(after, staff, change_set, name, old[name], new[name]) for name in names]
    return ChangeRecord.objects.bulk_create(records)


def password_changed(before: models.Model, after: models.Model) -> bool:
    return getattr(before, "password", None) != getattr(after, "password", None)


def field_change(instance, staff, change_set, name: str, old: Any, new: Any) -> ChangeRecord:
    return ChangeRecord(
        staff=staff,
        change_set=change_set,
        entity_type=str(instance._meta.model_name),
        entity_id=instance.pk,
        entity_label=label_of(instance),
        action=ChangeRecord.Action.UPDATED,
        field_name=name,
        old_value=old,
        new_value=new,
    )


def record_created(instance: models.Model, staff, change_set: uuid.UUID, **extra) -> ChangeRecord:
    return ChangeRecord.objects.create(
        staff=staff,
        change_set=change_set,
        entity_type=str(instance._meta.model_name),
        entity_id=instance.pk,
        entity_label=label_of(instance),
        action=ChangeRecord.Action.CREATED,
        new_value=snapshot(instance),
        **extra,
    )


def record_deleted(instance: models.Model, staff, change_set: uuid.UUID, **extra) -> ChangeRecord:
    return ChangeRecord.objects.create(
        staff=staff,
        change_set=change_set,
        entity_type=str(instance._meta.model_name),
        entity_id=instance.pk,
        entity_label=label_of(instance),
        action=ChangeRecord.Action.DELETED,
        old_value=snapshot(instance),
        **extra,
    )


def label_of(instance: models.Model) -> str:
    return str(instance)[:200]
