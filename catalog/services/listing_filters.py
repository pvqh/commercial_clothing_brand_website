"""Category listing filters read from and written back to the address (shopper-routes.md).

Every view has one normalised address so shared links reproduce it exactly (SC-004, R13).
"""

from dataclasses import dataclass, replace
from urllib.parse import urlencode

from django.db import models
from django.http import QueryDict
from django.utils.translation import gettext_lazy as _

from catalog.models import Size


class Sort(models.TextChoices):
    NEW = "new", _("Newest")
    PRICE_ASC = "price_asc", _("Price: low to high")
    PRICE_DESC = "price_desc", _("Price: high to low")


@dataclass(frozen=True)
class ListingFilters:
    sizes: tuple[Size, ...] = ()
    price_min: int | None = None
    price_max: int | None = None
    sort: Sort = Sort.NEW

    @classmethod
    def from_query(cls, query: QueryDict) -> "ListingFilters":
        price_min = whole_rubles(query.get("price_min"))
        price_max = whole_rubles(query.get("price_max"))
        if price_min is not None and price_max is not None and price_min > price_max:
            price_min, price_max = price_max, price_min
        return cls(
            sizes=known_sizes(query.getlist("size")),
            price_min=price_min,
            price_max=price_max,
            sort=chosen_sort(query.get("sort")),
        )

    @property
    def is_active(self) -> bool:
        """Sizes or a price range narrow the listing; sorting alone does not."""
        return bool(self.sizes) or self.has_price

    @property
    def has_price(self) -> bool:
        return self.price_min is not None or self.price_max is not None

    @property
    def is_default(self) -> bool:
        return not self.is_active and self.sort == Sort.NEW

    def params(self, page: int | None = None) -> list[tuple[str, str]]:
        """Parameters in the contract order: size, price_min, price_max, sort, page."""
        params = [("size", size.code) for size in self.sizes]
        if self.price_min is not None:
            params.append(("price_min", str(self.price_min)))
        if self.price_max is not None:
            params.append(("price_max", str(self.price_max)))
        if self.sort != Sort.NEW:
            params.append(("sort", self.sort))
        if page and page > 1:
            params.append(("page", str(page)))
        return params

    def query_string(self, page: int | None = None) -> str:
        params = self.params(page)
        return f"?{urlencode(params)}" if params else ""

    def without_size(self, size: Size) -> "ListingFilters":
        return replace(self, sizes=tuple(s for s in self.sizes if s != size))

    def without_price(self) -> "ListingFilters":
        return replace(self, price_min=None, price_max=None)


def chosen_sort(raw: str | None) -> Sort:
    return Sort(raw) if raw in Sort.values else Sort.NEW


def known_sizes(codes: list[str]) -> tuple[Size, ...]:
    sizes = {Size[code.upper()] for code in codes if code.upper() in Size.names}
    return tuple(sorted(sizes))


def whole_rubles(raw: str | None) -> int | None:
    if raw is None or not raw.strip().isdigit():
        return None
    return int(raw)
