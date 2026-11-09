"""Writing 2:3 photo renditions with Pillow alone (research R12).

This module imports nothing from Django, so the catalog import can run it in worker processes.
"""

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps

PHOTO_RATIO = 2 / 3
ENCODER_OPTIONS = {
    "avif": {"format": "AVIF", "quality": 60, "speed": 8},
    "webp": {"format": "WEBP", "quality": 80, "method": 4},
    "jpg": {"format": "JPEG", "quality": 82, "progressive": True, "optimize": True},
}


def rendition_height(width: int) -> int:
    return round(width / PHOTO_RATIO)


def write_rendition_files(source: Path, target_dir: Path, widths: list[int]) -> list[Path]:
    """Writes `<width>.<avif|webp|jpg>` into `target_dir` for every width; returns the paths."""
    image = load_cropped(source)
    target_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for width in widths:
        resized = image.resize((width, rendition_height(width)), Image.Resampling.LANCZOS)
        for extension, options in ENCODER_OPTIONS.items():
            path = target_dir / f"{width}.{extension}"
            path.write_bytes(encode(resized, options))
            written.append(path)
    return written


def load_cropped(source: Path) -> Image.Image:
    with Image.open(source) as image:
        upright = ImageOps.exif_transpose(image).convert("RGB")
    return crop_to_photo_ratio(upright)


def crop_to_photo_ratio(image: Image.Image) -> Image.Image:
    if abs(image.width / image.height - PHOTO_RATIO) < 0.01:
        return image
    target_height = min(image.height, rendition_height(image.width))
    target_width = round(target_height * PHOTO_RATIO)
    return ImageOps.fit(image, (target_width, target_height), centering=(0.5, 0.5))


def encode(image: Image.Image, options: dict) -> bytes:
    buffer = BytesIO()
    image.save(buffer, **options)
    return buffer.getvalue()
