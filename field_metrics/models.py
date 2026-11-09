from django.db import models
from django.utils.translation import gettext_lazy as _


class RumSample(models.Model):
    """One Core Web Vitals measurement from a shopper's browser (research R12).

    Holds no cookie, identifier or IP address; samples are deleted after 90 days.
    """

    class Metric(models.TextChoices):
        LCP = "LCP"
        INP = "INP"
        CLS = "CLS"

    class DeviceClass(models.TextChoices):
        MOBILE = "mobile", _("mobile")
        DESKTOP = "desktop", _("desktop")

    received_at = models.DateTimeField(auto_now_add=True, db_index=True)
    metric = models.CharField(max_length=3, choices=Metric)
    value = models.FloatField()
    route = models.CharField(max_length=50, help_text=_("Route name, never the full address"))
    device_class = models.CharField(max_length=7, choices=DeviceClass)

    class Meta:
        verbose_name = _("performance sample")
        verbose_name_plural = _("performance samples")

    def __str__(self) -> str:
        return f"{self.metric} {self.value:.3f} on {self.route} ({self.device_class})"
