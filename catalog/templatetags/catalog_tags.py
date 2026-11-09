from django import template
from django.core.files.storage import default_storage
from django.urls import translate_url
from django.utils.translation import get_language

from catalog.models import ProductPhoto
from catalog.models.translated import localized_value
from catalog.services.photo_renditions import rendition_path
from catalog.services.rendition_files import rendition_height

register = template.Library()

THOUSANDS_SEPARATOR = chr(0x202F)  # narrow no-break space
CURRENCY_SEPARATOR = chr(0x00A0)  # no-break space
SOURCE_FORMATS = (("image/avif", "avif"), ("image/webp", "webp"))


@register.filter
def localized(instance: object, field_name: str) -> str:
    return localized_value(instance, field_name)


@register.filter
def localized_slug(instance: object) -> str:
    language = "en" if (get_language() or "ru").startswith("en") else "ru"
    return getattr(instance, f"slug_{language}")


@register.filter
def rubles(kopecks: int | None) -> str:
    """`12500000` kopecks → `125 000 ₽` with a narrow no-break space between thousands (R15)."""
    if kopecks is None:
        return ""
    whole_rubles = round(kopecks / 100)
    grouped = f"{whole_rubles:,}".replace(",", THOUSANDS_SEPARATOR)
    return f"{grouped}{CURRENCY_SEPARATOR}₽"


@register.simple_tag(takes_context=True)
def alternate_url(context: template.Context, language: str) -> str:
    """Absolute address of the current page in `language`, as given by the view if it knows it."""
    request = context["request"]
    known = context.get("alternate_urls") or {}
    path = known.get(language) or translate_url(request.path, language)
    return request.build_absolute_uri(path)


@register.inclusion_tag("components/picture.html")
def picture(photo: ProductPhoto, sizes: str = "100vw", priority: bool = False) -> dict:
    widths = photo.rendition_widths()
    if not widths:
        return original_picture(photo, sizes, priority)
    return {
        "sources": [
            {"type": mime, "srcset": srcset(photo, widths, extension)}
            for mime, extension in SOURCE_FORMATS
        ],
        "src": rendition_url(photo, min(widths[-1], 720), "jpg"),
        "jpeg_srcset": srcset(photo, widths, "jpg"),
        "sizes": sizes,
        "width": widths[-1],
        "height": rendition_height(widths[-1]),
        "alt": photo.localized("alt_text"),
        "priority": priority,
    }


def original_picture(photo: ProductPhoto, sizes: str, priority: bool) -> dict:
    return {
        "sources": [],
        "src": photo.original.url,
        "sizes": sizes,
        "width": photo.width,
        "height": photo.height,
        "alt": photo.localized("alt_text"),
        "priority": priority,
    }


def srcset(photo: ProductPhoto, widths: list[int], extension: str) -> str:
    return ", ".join(f"{rendition_url(photo, width, extension)} {width}w" for width in widths)


def rendition_url(photo: ProductPhoto, width: int, extension: str) -> str:
    return default_storage.url(rendition_path(photo, width, extension))
