import pytest

from dpsprep.exceptions import DpsPrepConfigError
from dpsprep.ranges import RangeOption, RangeOptionGroup, parse_str_range_option


class TestParseStrRangeArgument:
    def test_without_range(self) -> None:
        assert parse_str_range_option('value') == RangeOption('value')

    def test_empty_range(self) -> None:
        with pytest.raises(DpsPrepConfigError):
            assert parse_str_range_option('value[]')

    def test_malformed_range(self) -> None:
        with pytest.raises(DpsPrepConfigError):
            assert parse_str_range_option('value[1-]')

    def test_range_with_only_start(self) -> None:
        assert parse_str_range_option('value[1]') == RangeOption('value', 1, 1)

    def test_unbounded_from_above_range(self) -> None:
        assert parse_str_range_option('value[1-end]') == RangeOption('value', 1)

    def test_bounded_range(self) -> None:
        assert parse_str_range_option('value[1-2]') == RangeOption('value', 1, 2)

    def test_tail(self) -> None:
        with pytest.raises(DpsPrepConfigError):
            assert parse_str_range_option('value[1-2]tail')


class TestRangeOptionGroup:
    def test_empty_group(self) -> None:
        group = RangeOptionGroup[str]([])
        assert group.get_value_for_one_based_page(3) is None
        assert group.get_global_value() is None

    def test_single_option(self) -> None:
        group = RangeOptionGroup([parse_str_range_option('a')])
        assert group.get_value_for_one_based_page(3) == 'a'
        assert group.get_global_value() == 'a'

    def test_single_option_with_index(self) -> None:
        group = RangeOptionGroup([parse_str_range_option('a[3]')])
        assert group.get_value_for_one_based_page(2) is None
        assert group.get_value_for_one_based_page(3) == 'a'
        assert group.get_global_value() is None

    def test_single_option_with_bounded_range(self) -> None:
        group = RangeOptionGroup([parse_str_range_option('a[3-4]')])
        assert group.get_value_for_one_based_page(2) is None
        assert group.get_value_for_one_based_page(3) == 'a'
        assert group.get_value_for_one_based_page(5) is None
        assert group.get_global_value() is None

    def test_single_option_with_unbounded_range(self) -> None:
        group = RangeOptionGroup([parse_str_range_option('a[3-end]')])
        assert group.get_value_for_one_based_page(2) is None
        assert group.get_value_for_one_based_page(3) == 'a'
        assert group.get_value_for_one_based_page(5) == 'a'
        assert group.get_global_value() is None

    def test_two_options(self) -> None:
        group = RangeOptionGroup([parse_str_range_option('a[1]'), parse_str_range_option('b[3-4]')])
        assert group.get_value_for_one_based_page(1) == 'a'
        assert group.get_value_for_one_based_page(2) is None
        assert group.get_value_for_one_based_page(3) == 'b'
        assert group.get_value_for_one_based_page(4) == 'b'
        assert group.get_value_for_one_based_page(5) is None
        assert group.get_global_value() is None
