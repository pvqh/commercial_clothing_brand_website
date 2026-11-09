from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, re_path
from django.views.static import serve

from catalog.seo.sitemaps import SITEMAPS
from catalog.views.robots import robots_txt
from field_metrics.views import rum_beacon

handler404 = "catalog.views.errors.not_found"

urlpatterns = [
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("robots.txt", robots_txt, name="robots"),
    path("staff/", admin.site.urls),
    path("rum/", rum_beacon, name="rum"),
]


def serve_media(request, path: str):
    """Uploaded photos in development and tests only; Caddy serves them in production."""
    return serve(request, path, document_root=str(settings.MEDIA_ROOT))


if settings.SERVE_MEDIA:
    media_prefix = settings.MEDIA_URL.strip("/")
    urlpatterns += [re_path(rf"^{media_prefix}/(?P<path>.*)$", serve_media)]

urlpatterns += i18n_patterns(
    path("", include("catalog.urls")),
    prefix_default_language=False,
)
