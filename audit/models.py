from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class ChangeRecord(models.Model):
    """One recorded change made in the staff area (FR-041, FR-042, Principle VIII).

    Append-only: a database trigger rejects deletes and every update except removing the staff
    member from records older than three years (FR-044).
    """

    class Action(models.TextChoices):
        CREATED = "created", _("created")
        UPDATED = "updated", _("changed")
        DELETED = "deleted", _("deleted")

    changed_at = models.DateTimeField(_("time"), default=timezone.now, db_index=True)
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        related_name="change_records",
        verbose_name=_("staff member"),
    )
    change_set = models.UUIDField(_("change set"))
    entity_type = models.CharField(_("item type"), max_length=50)
    entity_id = models.BigIntegerField(_("item id"))
    entity_label = models.CharField(_("item"), max_length=200)
    action = models.CharField(_("action"), max_length=10, choices=Action)
    # NULL (not "") marks "no field"; the check constraint below relies on it.
    field_name = models.CharField(_("field"), max_length=100, null=True, blank=True)  # noqa: DJ001
    old_value = models.JSONField(_("old value"), null=True, blank=True)
    new_value = models.JSONField(_("new value"), null=True, blank=True)
    undoes = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="undone_by",
        verbose_name=_("undoes"),
    )

    class Meta:
        ordering = ["-changed_at", "-id"]
        verbose_name = _("change")
        verbose_name_plural = _("change history")
        constraints = [
            models.CheckConstraint(
                condition=(Q(action="updated") & Q(field_name__isnull=False))
                | (~Q(action="updated") & Q(field_name__isnull=True)),
                name="changerecord_field_name_only_for_updates",
            ),
        ]
        indexes = [
            models.Index(fields=["entity_type", "entity_id", "changed_at"]),
            models.Index(fields=["staff", "changed_at"]),
            models.Index(fields=["change_set"]),
        ]

    def __str__(self) -> str:
        return f"{self.entity_label}: {self.get_action_display()}"
