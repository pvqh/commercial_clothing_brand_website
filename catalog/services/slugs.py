"""Readable Latin addresses for categories and products, and redirects from old ones (R7)."""

import re
from typing import Any

from django.utils.text import slugify

TRANSLITERATION = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh",
    "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts",
    "ч": "ch", "ш": "sh", "щ": "shch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu",
    "я": "ya",
}  # fmt: skip

LANGUAGES = ("ru", "en")


def slugify_ru(name: str) -> str:
    latin = "".join(TRANSLITERATION.get(letter, letter) for letter in name.lower())
    return slugify(latin)


def assign_slugs(instance: Any) -> None:
    """Sets `slug_ru` / `slug_en` from the names and records every replaced slug as a redirect."""
    base_ru = slugify_ru(instance.name_ru) or "item"
    base_en = slugify(instance.name_en) or base_ru
    for language, base in zip(LANGUAGES, (base_ru, base_en), strict=True):
        assign_slug(instance, language, base)


def assign_slug(instance: Any, language: str, base: str) -> None:
    field = f"slug_{language}"
    current = getattr(instance, field)
    if current and slug_belongs_to_base(current, base):
        return
    new_slug = unique_slug(instance, field, base)
    if current:
        record_redirect(instance, language, current)
    forget_redirect(instance, language, new_slug)
    setattr(instance, field, new_slug)


def slug_belongs_to_base(slug: str, base: str) -> bool:
    return slug == base or re.fullmatch(rf"{re.escape(base)}-\d+", slug) is not None


def unique_slug(instance: Any, field: str, base: str) -> str:
    max_length = int(type(instance)._meta.get_field(field).max_length)
    base = base[: max_length - 4].strip("-")
    candidate, suffix = base, 1
    while slug_is_taken(instance, field, candidate):
        suffix += 1
        candidate = f"{base}-{suffix}"
    return candidate


def slug_is_taken(instance: Any, field: str, candidate: str) -> bool:
    others = type(instance)._default_manager.exclude(pk=instance.pk)
    return others.filter(**{field: candidate}).exists()


def redirect_model(instance: Any) -> Any:
    return type(instance)._meta.get_field("slug_redirects").related_model


def record_redirect(instance: Any, language: str, old_slug: str) -> None:
    redirects = redirect_model(instance)._default_manager
    redirects.filter(language=language, old_slug=old_slug).delete()
    redirects.create(
        **{owner_field(instance): instance, "language": language, "old_slug": old_slug}
    )


def forget_redirect(instance: Any, language: str, slug: str) -> None:
    redirect_model(instance)._default_manager.filter(language=language, old_slug=slug).delete()


def owner_field(instance: Any) -> str:
    return str(type(instance)._meta.model_name)
