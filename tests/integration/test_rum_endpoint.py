import json
from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from field_metrics.models import RumSample

pytestmark = pytest.mark.django_db

VALID = {"metric": "LCP", "value": 1830.5, "route": "catalog:category", "device": "mobile"}


def post(client, body):
    payload = body if isinstance(body, str) else json.dumps(body)
    return client.post("/rum/", payload, content_type="application/json")


def test_a_valid_sample_is_stored_and_answered_with_204(client):
    response = post(client, VALID)
    assert response.status_code == 204
    assert RumSample.objects.get().route == "catalog:category"


def test_the_beacon_sets_no_cookie(client):
    assert not post(client, VALID).cookies


@pytest.mark.parametrize(
    "body",
    [
        "not json",
        [1, 2],
        VALID | {"metric": "FID"},
        VALID | {"value": "fast"},
        VALID | {"value": -1},
        VALID | {"route": "/katalog/shuby/?size=m"},
        VALID | {"device": "tablet"},
    ],
)
def test_an_invalid_sample_is_rejected_with_400(client, body):
    assert post(client, body).status_code == 400
    assert not RumSample.objects.exists()


def test_a_get_request_is_refused(client):
    assert client.get("/rum/").status_code == 405


def test_nothing_identifying_is_stored(client):
    post(client, VALID | {"user": "anna", "url": "https://example.com/?email=a@b.c"})
    stored = {field.name for field in RumSample._meta.fields}
    assert stored == {"id", "received_at", "metric", "value", "route", "device_class"}


def test_samples_older_than_90_days_are_purged(client):
    post(client, VALID)
    post(client, VALID)
    RumSample.objects.filter(pk=RumSample.objects.first().pk).update(
        received_at=timezone.now() - timedelta(days=91)
    )
    call_command("purge_rum_samples")
    assert RumSample.objects.count() == 1
