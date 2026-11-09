"""SC-008: the 200-product launch catalog loads in under 15 minutes. Run with `-m slow`."""

import time

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from catalog.models import Product
from tests.fixtures.build_catalog_200 import PRODUCT_COUNT, build_catalog_200

TIME_LIMIT_SECONDS = 15 * 60


@pytest.mark.slow
@pytest.mark.django_db(transaction=True)
def test_a_200_product_catalog_imports_within_15_minutes(tmp_path):
    get_user_model().objects.create_superuser("admin", password="a-long-password-1")
    workbook, photos = build_catalog_200(tmp_path)

    started = time.monotonic()
    call_command("import_catalog", str(workbook), "--photos", str(photos), "--run-by", "admin")
    elapsed = time.monotonic() - started

    assert Product.objects.filter(is_published=True).count() == PRODUCT_COUNT
    assert elapsed < TIME_LIMIT_SECONDS, f"Import took {elapsed:.0f} s"
