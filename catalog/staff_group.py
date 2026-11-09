"""The "Catalog staff" group: all catalog permissions, none for user management (research R8).

Migration 0002 creates it on deploy; `ensure_staff_group` recreates it if it is ever missing.
"""

from django.contrib.auth.models import Group, Permission
from django.db.models import Q

STAFF_GROUP = "Catalog staff"
CATALOG_MODELS = [
    "category",
    "product",
    "productcategory",
    "color",
    "variant",
    "productphoto",
    "producttype",
    "sizeguide",
    "sizeguiderow",
]
DELETABLE_MODELS = ["productcategory", "color", "variant", "productphoto", "sizeguiderow"]


def staff_codenames() -> list[str]:
    actions = ("add", "change", "view")
    codenames = [f"{action}_{model}" for model in CATALOG_MODELS for action in actions]
    return codenames + [f"delete_{model}" for model in DELETABLE_MODELS]


def ensure_staff_group() -> Group:
    group, created = Group.objects.get_or_create(name=STAFF_GROUP)
    if created:
        catalog = Q(content_type__app_label="catalog", codename__in=staff_codenames())
        history = Q(content_type__app_label="audit", codename="view_changerecord")
        group.permissions.set(Permission.objects.filter(catalog | history))
    return group
