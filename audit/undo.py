"""Undoing a recorded change, following the Undo rules in data-model.md (FR-042, research R9)."""

import uuid
from typing import Any

from django.apps import apps
from django.db import models, router, transaction
from django.db.models.deletion import Collector, ProtectedError, RestrictedError
from django.utils.translation import gettext as _

from .models import ChangeRecord
from .recording import field_change, new_change_set, record_created, record_deleted, snapshot


class UndoRefused(Exception):
    """The change cannot be undone; the message tells staff why, in Russian."""


def undo(record: ChangeRecord, staff) -> list[ChangeRecord]:
    """Reverses `record` in one transaction and returns the new records, all with `undoes` set."""
    handlers = {
        ChangeRecord.Action.UPDATED: undo_update,
        ChangeRecord.Action.DELETED: undo_delete,
        ChangeRecord.Action.CREATED: undo_create,
    }
    with transaction.atomic():
        return handlers[ChangeRecord.Action(record.action)](record, staff, new_change_set())


def model_of(record: ChangeRecord) -> type[models.Model]:
    for model in apps.get_models():
        if model._meta.model_name == record.entity_type:
            return model
    raise UndoRefused(_("This kind of item can no longer be changed."))


def stored_row(record: ChangeRecord) -> models.Model:
    instance = model_of(record)._default_manager.filter(pk=record.entity_id).first()
    if instance is None:
        raise UndoRefused(_("This item no longer exists."))
    return instance


def undo_update(record: ChangeRecord, staff, change_set: uuid.UUID) -> list[ChangeRecord]:
    instance = stored_row(record)
    field_name = str(record.field_name)
    current = snapshot(instance).get(field_name)
    if field_name == "password" or current != record.new_value:
        raise UndoRefused(_("This value has changed since; undo the later change first."))
    set_column(instance, field_name, record.old_value)
    instance.save()
    undo_record = field_change(instance, staff, change_set, field_name, current, record.old_value)
    undo_record.undoes = record
    undo_record.save()
    return [undo_record]


def undo_delete(record: ChangeRecord, staff, change_set: uuid.UUID) -> list[ChangeRecord]:
    model = model_of(record)
    if model._default_manager.filter(pk=record.entity_id).exists():
        raise UndoRefused(_("An item with this number exists again, so it cannot be restored."))
    instance = model(**column_values(model, record.old_value or {}))
    refuse_if_parent_missing(instance)
    instance.save(force_insert=True)
    return [record_created(instance, staff, change_set, undoes=record)]


def undo_create(record: ChangeRecord, staff, change_set: uuid.UUID) -> list[ChangeRecord]:
    instance = stored_row(record)
    doomed = rows_deleted_with(instance)
    undo_records = [record_deleted(row, staff, change_set, undoes=record) for row in doomed]
    instance.delete()
    return undo_records


def set_column(instance: models.Model, attname: str, json_value: Any) -> None:
    field = column(type(instance), attname)
    setattr(instance, attname, field.to_python(json_value))


def column(model: type[models.Model], attname: str) -> models.Field:
    return next(field for field in model._meta.concrete_fields if field.attname == attname)


def column_values(model: type[models.Model], stored: dict[str, Any]) -> dict[str, Any]:
    return {
        field.attname: field.to_python(stored[field.attname])
        for field in model._meta.concrete_fields
        if field.attname in stored
    }


def refuse_if_parent_missing(instance: models.Model) -> None:
    for field in instance._meta.concrete_fields:
        parent_id = getattr(instance, field.attname) if field.is_relation else None
        if parent_id is not None and not parent_exists(field, parent_id):
            raise UndoRefused(
                _("The item it belonged to has been deleted, so it cannot be restored.")
            )


def parent_exists(field: models.Field, parent_id: Any) -> bool:
    parent_model = field.related_model
    assert isinstance(parent_model, type)  # concrete relations always point at a model class
    return parent_model._default_manager.filter(pk=parent_id).exists()


def rows_deleted_with(instance: models.Model) -> list[models.Model]:
    """The row and every row that deleting it would delete too (cascades)."""
    collector = Collector(using=router.db_for_write(type(instance)))
    try:
        collector.collect([instance])
    except (ProtectedError, RestrictedError) as blocked:
        raise UndoRefused(
            _("Other items still use this one, so it cannot be removed.")
        ) from blocked
    rows = [row for model_rows in collector.data.values() for row in model_rows]
    rows += [row for queryset in collector.fast_deletes for row in queryset]
    return rows
