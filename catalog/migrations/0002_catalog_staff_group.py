"""Creates the "Catalog staff" group: every catalog permission, no user-management permission.

Staff may delete only the rows they manage inside a product (colors, sizes, photos, category
memberships and size-guide rows); products and categories are unpublished instead (research R8).
"""

from django.contrib.auth.management import create_permissions
from django.db import migrations

GROUP_NAME = "Catalog staff"
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


def wanted_codenames() -> list[str]:
    codenames = [f"{action}_{model}" for model in CATALOG_MODELS for action in ("add", "change", "view")]
    codenames += [f"delete_{model}" for model in DELETABLE_MODELS]
    return codenames


def ensure_permissions_exist(apps) -> None:
    """Permissions are normally created after migrations; this group needs them now."""
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, verbosity=0)
        app_config.models_module = None


def create_group(apps, schema_editor) -> None:
    ensure_permissions_exist(apps)
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    group, _created = Group.objects.get_or_create(name=GROUP_NAME)
    catalog_permissions = Permission.objects.filter(
        content_type__app_label="catalog", codename__in=wanted_codenames()
    )
    history_permission = Permission.objects.filter(
        content_type__app_label="audit", codename="view_changerecord"
    )
    group.permissions.set([*catalog_permissions, *history_permission])


def remove_group(apps, schema_editor) -> None:
    apps.get_model("auth", "Group").objects.filter(name=GROUP_NAME).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
        ("audit", "0002_append_only_trigger"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [migrations.RunPython(create_group, remove_group)]
