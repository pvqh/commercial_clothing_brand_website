from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_GET

from .caching import public_cache


@require_GET
@public_cache
def robots_txt(request: HttpRequest) -> HttpResponse:
    lines = [
        "User-agent: *",
        "Disallow: /staff/",
        "Disallow: /rum/",
        "",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; charset=utf-8")
