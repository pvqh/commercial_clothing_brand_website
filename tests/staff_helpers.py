"""Helpers for staff-area tests: accounts and posting Django admin change forms."""

from django.contrib.auth import get_user_model
from django.forms import BaseForm

from catalog.staff_group import ensure_staff_group

STAFF_PASSWORD = "a-long-staff-password-1"


def create_staff(username: str = "staff", **fields):
    user = get_user_model().objects.create_user(
        username, password=STAFF_PASSWORD, is_staff=True, first_name="Анна", **fields
    )
    user.groups.add(ensure_staff_group())
    return user


def create_admin(username: str = "admin"):
    return get_user_model().objects.create_superuser(username, password=STAFF_PASSWORD)


def change_form_data(response) -> dict:
    """The POST data that resubmits an admin change form exactly as rendered."""
    data: dict = {}
    add_form_values(data, response.context["adminform"].form)
    for inline in response.context["inline_admin_formsets"]:
        add_form_values(data, inline.formset.management_form)
        for form in inline.formset.forms:
            add_form_values(data, form)
    return data


def add_form_values(data: dict, form: BaseForm) -> None:
    for name in form.fields:
        value = form[name].value()
        key = form.add_prefix(name)
        if value is None or hasattr(value, "url") or hasattr(value, "file"):
            continue
        if isinstance(value, bool):
            if value:
                data[key] = "on"
        else:
            data[key] = value


def inline_formset(response, model_name: str):
    for inline in response.context["inline_admin_formsets"]:
        if inline.formset.model._meta.model_name == model_name:
            return inline.formset
    raise LookupError(f"No inline for {model_name}")


def inline_prefix(response, model_name: str) -> str:
    return inline_formset(response, model_name).prefix
