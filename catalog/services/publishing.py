"""Publishing products only when they meet the publish rules in data-model.md."""

from django.utils import timezone
from django.utils.translation import gettext as _

from catalog.models import Product


class PublishRuleError(Exception):
    """A product cannot be published; `failures` lists every broken rule, in Russian for staff."""

    def __init__(self, product: Product, failures: list[str]):
        self.product = product
        self.failures = failures
        super().__init__(f"{product}: " + "; ".join(failures))


def publish(product: Product) -> None:
    failures = broken_publish_rules(product)
    if failures:
        raise PublishRuleError(product, failures)
    product.is_published = True
    product.first_published_at = product.first_published_at or timezone.now()
    product.save()


def unpublish(product: Product) -> None:
    product.is_published = False
    product.save()


def broken_publish_rules(product: Product) -> list[str]:
    checks = [
        (has_category, _("Add the product to at least one category.")),
        (has_buyable_color, _("Add at least one color with at least one size.")),
        (
            has_described_photos,
            _("Add at least one photo and alt text in Russian for every photo."),
        ),
        (has_russian_texts, _("Fill in every required Russian text and the product type.")),
        (has_size_guide_if_sized, _("Choose a size guide: the product type has none.")),
    ]
    return [str(message) for check, message in checks if not check(product)]


def has_category(product: Product) -> bool:
    return product.category_memberships.exists()


def has_buyable_color(product: Product) -> bool:
    return product.variants.exists()


def has_described_photos(product: Product) -> bool:
    photos = product.photos.all()
    return photos.exists() and not photos.filter(alt_text_ru="").exists()


def has_russian_texts(product: Product) -> bool:
    return product.product_type_id is not None and not product.missing_russian_fields()


def has_size_guide_if_sized(product: Product) -> bool:
    return product.is_one_size or product.effective_size_guide is not None
