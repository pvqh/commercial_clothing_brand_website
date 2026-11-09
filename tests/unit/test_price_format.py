from django.utils import translation

from catalog.templatetags.catalog_tags import rubles

NARROW_NBSP = chr(0x202F)
NBSP = chr(0x00A0)


def test_kopecks_are_shown_as_whole_rubles_with_grouped_thousands():
    assert rubles(12_500_000) == f"125{NARROW_NBSP}000{NBSP}₽"


def test_prices_under_a_thousand_rubles_have_no_separator():
    assert rubles(95_000) == f"950{NBSP}₽"


def test_millions_are_grouped_twice():
    assert rubles(123_456_700) == f"1{NARROW_NBSP}234{NARROW_NBSP}567{NBSP}₽"


def test_format_is_the_same_on_english_pages():
    with translation.override("en"):
        assert rubles(12_500_000) == f"125{NARROW_NBSP}000{NBSP}₽"
