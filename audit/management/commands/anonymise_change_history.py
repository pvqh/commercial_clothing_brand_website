from django.core.management.base import BaseCommand
from django.utils import timezone

from audit.models import ChangeRecord


def three_years_before(moment):
    try:
        return moment.replace(year=moment.year - 3)
    except ValueError:  # 29 February
        return moment.replace(year=moment.year - 3, day=28)


class Command(BaseCommand):
    help = "Removes the staff member from change records older than three years (FR-044)."

    def handle(self, *args, **options) -> None:
        cutoff = three_years_before(timezone.now())
        old_records = ChangeRecord.objects.filter(changed_at__lt=cutoff, staff__isnull=False)
        count = old_records.update(staff=None)
        self.stdout.write(f"Anonymised {count} change records.")
