from datetime import timedelta

from axes.models import AccessAttempt, AccessFailureLog
from django.core.management.base import BaseCommand
from django.utils import timezone

KEEP_FOR = timedelta(hours=24)


class Command(BaseCommand):
    help = "Deletes failed sign-in records older than 24 hours (research R10)."

    def handle(self, *args, **options) -> None:
        cutoff = timezone.now() - KEEP_FOR
        attempts, _ = AccessAttempt.objects.filter(attempt_time__lt=cutoff).delete()
        failures, _ = AccessFailureLog.objects.filter(attempt_time__lt=cutoff).delete()
        self.stdout.write(f"Deleted {attempts + failures} sign-in records.")
