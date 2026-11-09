"""Responsive photo files for a ProductPhoto: 2:3 renditions in AVIF, WebP and JPEG (R12).

Renditions live next to the media files at `photos/<id>/<width>.<format>`; they are files only,
never database rows. Production stores media on the local volume served by Caddy (R17).
"""

from pathlib import Path

from django.conf import settings

from catalog.models import ProductPhoto

from .rendition_files import write_rendition_files

RenditionJob = tuple[Path, Path, list[int]]


def rendition_path(photo: ProductPhoto, width: int, extension: str) -> str:
    return f"photos/{photo.pk}/{width}.{extension}"


def rendition_job(photo: ProductPhoto) -> RenditionJob:
    """(source file, target folder, widths): everything a worker process needs."""
    target_dir = Path(settings.MEDIA_ROOT) / "photos" / str(photo.pk)
    return Path(photo.original.path), target_dir, photo.rendition_widths()


def generate_renditions(photo: ProductPhoto) -> list[str]:
    """Writes every rendition of the photo and returns their media-relative paths."""
    written = write_rendition_files(*rendition_job(photo))
    media_root = Path(settings.MEDIA_ROOT)
    return [path.relative_to(media_root).as_posix() for path in written]
