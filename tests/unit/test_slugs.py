import pytest

from catalog.demo_catalog import build_category, build_product
from catalog.models import ProductSlugRedirect
from catalog.services.slugs import slugify_ru


def test_russian_name_is_transliterated_to_latin():
    assert slugify_ru("Шуба из норки") == "shuba-iz-norki"


def test_letters_with_multi_character_transliterations():
    assert slugify_ru("Щука, ёж и Юля") == "shchuka-ezh-i-yulya"


@pytest.mark.django_db
def test_english_slug_comes_from_the_english_name():
    product = build_product(name_ru="Шуба из норки", name_en="Mink coat")
    assert product.slug_en == "mink-coat"


@pytest.mark.django_db
def test_english_slug_falls_back_to_the_russian_slug():
    product = build_product(name_ru="Шуба из норки", name_en="")
    assert product.slug_en == "shuba-iz-norki"


@pytest.mark.django_db
def test_clashing_slug_gets_a_numeric_suffix():
    build_product(name_ru="Шуба из норки")
    second = build_product(name_ru="Шуба из норки")
    assert second.slug_ru == "shuba-iz-norki-2"


@pytest.mark.django_db
def test_rename_keeps_the_previous_slug_as_a_redirect():
    product = build_product(name_ru="Шуба из норки")
    product.name_ru = "Шуба из соболя"
    product.save()
    assert ProductSlugRedirect.objects.filter(
        product=product, language="ru", old_slug="shuba-iz-norki"
    ).exists()


@pytest.mark.django_db
def test_saving_without_a_rename_keeps_the_slug():
    category = build_category(name_ru="Шубы")
    category.position = 5
    category.save()
    assert category.slug_ru == "shuby" and not category.slug_redirects.exists()
