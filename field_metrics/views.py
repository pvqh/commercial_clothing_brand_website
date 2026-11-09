"""`POST /rum/`: the field Core Web Vitals beacon (contracts/shopper-routes.md "RUM beacon")."""

import json
import math
import re

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import RumSample

ROUTE_NAME = re.compile(r"[a-z_]+:[a-z_]+")


class InvalidSample(ValueError):
    pass


@csrf_exempt  # Anonymous beacon that only adds a counter row; there is no session to protect.
@require_POST
def rum_beacon(request: HttpRequest) -> HttpResponse:
    try:
        sample = parse_sample(request.body)
    except InvalidSample:
        return HttpResponseBadRequest()
    sample.save()
    return HttpResponse(status=204)


def parse_sample(body: bytes) -> RumSample:
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError) as broken:
        raise InvalidSample("Body is not JSON") from broken
    if not isinstance(data, dict):
        raise InvalidSample("Body is not an object")
    return RumSample(
        metric=choice(data.get("metric"), RumSample.Metric.values),
        value=metric_value(data.get("value")),
        route=route_name(data.get("route")),
        device_class=choice(data.get("device"), RumSample.DeviceClass.values),
    )


def choice(value, allowed: list[str]) -> str:
    if value not in allowed:
        raise InvalidSample(f"Unexpected value {value!r}")
    return value


def metric_value(value) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise InvalidSample("Value is not a number")
    if not math.isfinite(value) or value < 0:
        raise InvalidSample("Value is out of range")
    return float(value)


def route_name(value) -> str:
    if not isinstance(value, str) or len(value) > 50 or not ROUTE_NAME.fullmatch(value):
        raise InvalidSample("Route is not a route name")
    return value
