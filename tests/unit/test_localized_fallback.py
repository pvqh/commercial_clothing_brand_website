from types import SimpleNamespace

from django.utils import translation

from catalog.models.translated import localized_value


def make_record(name_ru: str, name_en: str) -> SimpleNamespace:
    return SimpleNamespace(name_ru=name_ru, name_en=name_en)


def test_english_value_is_returned_on_english_pages():
    with translation.override("en"):
        assert localized_value(make_record("Шуба", "Coat"), "name") == "Coat"


def test_russian_value_is_returned_on_english_pages_when_english_is_blank():
    with translation.override("en"):
        assert localized_value(make_record("Шуба", "  "), "name") == "Шуба"


def test_russian_value_is_always_returned_on_russian_pages():
    with translation.override("ru"):
        assert localized_value(make_record("Шуба", "Coat"), "name") == "Шуба"
