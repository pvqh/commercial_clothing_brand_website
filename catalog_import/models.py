from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


class CatalogImport(models.Model):
    """One load of the launch catalog from a workbook (User Story 5, FR-030–FR-032)."""

    class Status(models.TextChoices):
        RUNNING = "running", _("running")
        COMPLETED = "completed", _("completed")
        FAILED = "failed", _("failed")

    started_at = models.DateTimeField(_("started"), auto_now_add=True)
    finished_at = models.DateTimeField(_("finished"), null=True, blank=True)
    status = models.CharField(_("status"), max_length=10, choices=Status, default=Status.RUNNING)
    source_filename = models.CharField(_("workbook"), max_length=255)
    run_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name=_("run by")
    )
    products_published = models.PositiveIntegerField(_("products published"), default=0)
    products_draft = models.PositiveIntegerField(_("products saved as drafts"), default=0)
    rows_rejected = models.PositiveIntegerField(_("rows rejected"), default=0)
    problems = models.JSONField(_("problems"), default=list, blank=True)

    class Meta:
        ordering = ["-started_at"]
        verbose_name = _("catalog import")
        verbose_name_plural = _("catalog imports")
        constraints = [
            models.CheckConstraint(
                condition=Q(status="running") | Q(finished_at__isnull=False),
                name="catalogimport_finished_when_done",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.source_filename} ({self.get_status_display()})"
