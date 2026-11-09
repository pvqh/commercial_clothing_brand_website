"""Staff-area screens for the catalog (contracts/staff-area.md). Mounted at /staff/."""

from django.contrib import admin
from django.utils.translation import gettext_lazy

from . import category, product, size_guide, staff_accounts  # noqa: F401  (registers screens)

admin.site.site_header = gettext_lazy("Catalog: staff area")
admin.site.site_title = gettext_lazy("Staff area")
admin.site.index_title = gettext_lazy("Catalog management")
admin.site.site_url = "/"
