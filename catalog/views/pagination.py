from collections.abc import Callable
from dataclasses import dataclass

from django.core.paginator import Page

PRODUCTS_PER_PAGE = 24


def normalised_page(raw: str | None, page_count: int) -> int | None:
    """The page to show for `?page=<raw>`: None for page 1, never past the last page (R13)."""
    if raw is None or not raw.isdigit():
        return None
    page = min(int(raw), page_count)
    return page if page >= 2 else None


@dataclass(frozen=True)
class PageLink:
    number: int
    url: str
    is_current: bool


@dataclass(frozen=True)
class PageNavigation:
    links: list[PageLink]
    previous_url: str
    next_url: str


def page_navigation(page: Page, url_for: Callable[[int], str]) -> PageNavigation:
    return PageNavigation(
        links=[
            PageLink(number=number, url=url_for(number), is_current=number == page.number)
            for number in page.paginator.page_range
        ],
        previous_url=url_for(page.previous_page_number()) if page.has_previous() else "",
        next_url=url_for(page.next_page_number()) if page.has_next() else "",
    )
