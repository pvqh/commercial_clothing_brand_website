from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from field_metrics.models import RumSample

KEEP_FOR = timedelta(days=90)


class Command(BaseCommand):
    help = "Deletes performance samples older than 90 days (research R12)."

    def handle(self, *args, **options) -> None:
        deleted, _ = RumSample.objects.filter(received_at__lt=timezone.now() - KEEP_FOR).delete()
        self.stdout.write(f"Deleted {deleted} performance samples.")
