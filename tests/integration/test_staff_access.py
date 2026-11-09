from datetime import timedelta

import pytest
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError
from django.utils import timezone

from catalog.demo_catalog import build_product
from tests.staff_helpers import STAFF_PASSWORD, create_admin, create_staff

pytestmark = pytest.mark.django_db

LOGIN_URL = "/staff/login/"
PRODUCTS_URL = "/staff/catalog/product/"


def sign_in(client, username: str, password: str):
    return client.post(LOGIN_URL, {"username": username, "password": password, "next": "/staff/"})


def is_signed_in(client) -> bool:
    return client.get("/staff/").status_code == 200


def error_text(response) -> str:
    return " ".join(str(error) for error in response.context["form"].non_field_errors())


def test_anonymous_visitors_are_sent_to_sign_in_without_catalog_data(client):
    product = build_product(name_ru="Секретная шуба")
    response = client.get(PRODUCTS_URL)
    assert response.status_code == 302 and response["Location"].startswith(LOGIN_URL)
    assert product.name_ru not in response.content.decode()


def test_staff_can_sign_in(client):
    create_staff()
    sign_in(client, "staff", STAFF_PASSWORD)
    assert is_signed_in(client)


def test_a_disabled_account_gets_the_wrong_password_message(client):
    create_staff("disabled", is_active=False)
    create_staff("active")
    disabled = sign_in(client, "disabled", STAFF_PASSWORD)
    wrong = sign_in(client, "active", "not-the-password")
    assert error_text(disabled) == error_text(wrong) and not is_signed_in(client)


def test_five_wrong_passwords_lock_the_username(client):
    create_staff()
    for _ in range(5):
        sign_in(client, "staff", "wrong-password")
    sign_in(client, "staff", STAFF_PASSWORD)
    assert not is_signed_in(client)


def test_a_successful_sign_in_resets_the_failure_count(client):
    create_staff()
    for _ in range(4):
        sign_in(client, "staff", "wrong-password")
    sign_in(client, "staff", STAFF_PASSWORD)
    client.logout()
    for _ in range(4):
        sign_in(client, "staff", "wrong-password")
    sign_in(client, "staff", STAFF_PASSWORD)
    assert is_signed_in(client)


def test_lockout_lasts_fifteen_minutes():
    assert timedelta(minutes=15) == settings.AXES_COOLOFF_TIME


def test_a_session_ends_after_two_hours_without_requests(client):
    create_staff()
    sign_in(client, "staff", STAFF_PASSWORD)
    assert settings.SESSION_COOKIE_AGE == 7200 and settings.SESSION_SAVE_EVERY_REQUEST
    Session.objects.update(expire_date=timezone.now() - timedelta(seconds=1))
    assert not is_signed_in(client)


def test_a_password_shorter_than_twelve_characters_is_rejected():
    with pytest.raises(ValidationError):
        validate_password("Shrt-pass-1")


def test_staff_cannot_open_the_staff_accounts_screen(client):
    client.force_login(create_staff())
    assert client.get("/staff/auth/user/").status_code == 403


def test_nobody_can_delete_a_staff_account(client):
    admin = create_admin()
    staff = create_staff()
    client.force_login(admin)
    assert client.get(f"/staff/auth/user/{staff.pk}/delete/").status_code == 403


def test_staff_responses_are_not_indexed(client):
    assert client.get(LOGIN_URL)["X-Robots-Tag"] == "noindex"


def test_the_staff_area_is_in_russian(client):
    assert 'lang="ru"' in client.get(LOGIN_URL, HTTP_ACCEPT_LANGUAGE="en").content.decode()
