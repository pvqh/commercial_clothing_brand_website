from django.http import QueryDict

from catalog.models import Size
from catalog.services.listing_filters import ListingFilters, Sort


def parse(query: str) -> ListingFilters:
    return ListingFilters.from_query(QueryDict(query))


def test_sizes_are_read_from_their_codes():
    assert parse("size=m&size=l").sizes == (Size.M, Size.L)


def test_unknown_sizes_are_dropped():
    assert parse("size=zz&size=m").sizes == (Size.M,)


def test_sizes_are_sorted_by_the_size_scale_and_deduplicated():
    assert parse("size=xl&size=s&size=xl").sizes == (Size.S, Size.XL)


def test_non_numeric_prices_are_dropped():
    assert parse("price_min=abc&price_max=-5").price_min is None


def test_a_minimum_above_the_maximum_is_swapped():
    filters = parse("price_min=200000&price_max=100000")
    assert (filters.price_min, filters.price_max) == (100000, 200000)


def test_an_unknown_sort_falls_back_to_newest():
    assert parse("sort=cheapest").sort == Sort.NEW


def test_the_default_sort_is_left_out_of_the_address():
    assert parse("sort=new").query_string() == ""


def test_parameters_are_written_in_the_contract_order():
    filters = parse("sort=price_asc&price_max=200000&size=l&price_min=1000")
    assert filters.query_string(page=2) == (
        "?size=l&price_min=1000&price_max=200000&sort=price_asc&page=2"
    )


def test_the_query_string_round_trips():
    query = "?size=s&size=m&price_min=5000&sort=price_desc"
    assert parse(query.removeprefix("?")).query_string() == query


def test_filters_are_active_when_a_size_or_price_is_chosen():
    assert parse("size=m").is_active and parse("price_max=5").is_active


def test_sorting_alone_is_not_a_filter():
    assert not parse("sort=price_asc").is_active


def test_removing_a_size_keeps_the_other_filters():
    filters = parse("size=m&size=l&price_min=10")
    assert filters.without_size(Size.M).query_string() == "?size=l&price_min=10"


def test_removing_the_price_keeps_the_sizes():
    assert parse("size=m&price_min=10&price_max=20").without_price().query_string() == "?size=m"
