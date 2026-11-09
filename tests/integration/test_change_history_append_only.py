from datetime import timedelta
from uuid import uuid4

import pytest
from django.core.management import call_command
from django.db import DatabaseError, connection, transaction
from django.utils import timezone

from audit.models import ChangeRecord
from tests.staff_helpers import create_staff

pytestmark = pytest.mark.django_db


def make_record(staff, age: timedelta) -> ChangeRecord:
    return ChangeRecord.objects.create(
        changed_at=timezone.now() - age,
        staff=staff,
        change_set=uuid4(),
        entity_type="category",
        entity_id=1,
        entity_label="Шубы",
        action="updated",
        field_name="name_ru",
        old_value="Шубы",
        new_value="Меха",
    )


def run_sql(sql: str, params: list) -> None:
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute(sql, params)


@pytest.fixture
def staff():
    return create_staff()


def test_records_cannot_be_updated_with_raw_sql(staff):
    record = make_record(staff, timedelta(days=1))
    with pytest.raises(DatabaseError):
        run_sql("UPDATE audit_changerecord SET new_value = '\"x\"' WHERE id = %s", [record.pk])


def test_records_cannot_be_deleted_with_raw_sql(staff):
    record = make_record(staff, timedelta(days=1))
    with pytest.raises(DatabaseError):
        run_sql("DELETE FROM audit_changerecord WHERE id = %s", [record.pk])


def test_the_staff_name_of_a_recent_record_cannot_be_removed(staff):
    record = make_record(staff, timedelta(days=30))
    with pytest.raises(DatabaseError):
        run_sql("UPDATE audit_changerecord SET staff_id = NULL WHERE id = %s", [record.pk])


def test_the_staff_name_of_a_record_older_than_three_years_can_be_removed(staff):
    record = make_record(staff, timedelta(days=3 * 366))
    run_sql("UPDATE audit_changerecord SET staff_id = NULL WHERE id = %s", [record.pk])
    record.refresh_from_db()
    assert record.staff_id is None


def test_anonymising_removes_names_only_from_records_older_than_three_years(staff):
    old = make_record(staff, timedelta(days=3 * 366))
    recent = make_record(staff, timedelta(days=30))
    call_command("anonymise_change_history")
    old.refresh_from_db()
    recent.refresh_from_db()
    assert (old.staff_id, recent.staff_id) == (None, staff.pk)
