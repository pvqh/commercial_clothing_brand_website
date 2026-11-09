"""Makes the change history append-only in the database itself (research R9, Principle VIII).

DELETE is always rejected. UPDATE is rejected unless the only change is setting staff_id to NULL
on a record older than three years (the FR-044 name removal).
"""

from django.db import migrations

CREATE_TRIGGER = """
CREATE FUNCTION audit_changerecord_append_only() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'The change history is append-only: records cannot be deleted';
    END IF;
    IF OLD.staff_id IS NOT NULL
       AND NEW.staff_id IS NULL
       AND OLD.changed_at < now() - interval '3 years'
       AND (to_jsonb(NEW) - 'staff_id') = (to_jsonb(OLD) - 'staff_id') THEN
        RETURN NEW;
    END IF;
    RAISE EXCEPTION 'The change history is append-only: records cannot be changed';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_changerecord_append_only
BEFORE UPDATE OR DELETE ON audit_changerecord
FOR EACH ROW EXECUTE FUNCTION audit_changerecord_append_only();
"""

DROP_TRIGGER = """
DROP TRIGGER IF EXISTS audit_changerecord_append_only ON audit_changerecord;
DROP FUNCTION IF EXISTS audit_changerecord_append_only();
"""


class Migration(migrations.Migration):
    dependencies = [("audit", "0001_initial")]

    operations = [migrations.RunSQL(CREATE_TRIGGER, reverse_sql=DROP_TRIGGER)]
