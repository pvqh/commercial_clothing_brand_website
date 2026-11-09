import pytest
from django.core.files.storage import default_storage
from PIL import Image

from catalog.demo_catalog import build_photo
from catalog.services.photo_renditions import generate_renditions, rendition_path

FORMATS = ("avif", "webp", "jpg")


@pytest.mark.django_db
def test_large_source_produces_every_width_in_every_format():
    photo = build_photo(width=1600, height=2400)
    generate_renditions(photo)
    for width in (360, 720, 1080, 1440):
        for extension in FORMATS:
            assert default_storage.exists(rendition_path(photo, width, extension))


@pytest.mark.django_db
def test_narrow_source_produces_only_widths_up_to_its_own():
    photo = build_photo(width=900, height=1350)
    written = generate_renditions(photo)
    assert sorted({int(path.rsplit("/", 1)[1].split(".")[0]) for path in written}) == [360, 720]


@pytest.mark.django_db
def test_no_rendition_is_wider_than_the_original():
    photo = build_photo(width=900, height=1350)
    for path in generate_renditions(photo):
        with default_storage.open(path) as rendition, Image.open(rendition) as image:
            assert image.width <= 900


@pytest.mark.django_db
def test_renditions_are_cropped_to_two_by_three():
    photo = build_photo(width=1000, height=1000)
    generate_renditions(photo)
    with default_storage.open(rendition_path(photo, 360, "jpg")) as file, Image.open(file) as image:
        assert (image.width, image.height) == (360, 540)


@pytest.mark.django_db
def test_square_source_offers_only_widths_that_fit_after_cropping():
    assert build_photo(width=1000, height=1000).rendition_widths() == [360]
